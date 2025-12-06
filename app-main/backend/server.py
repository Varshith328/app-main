from fastapi import FastAPI, APIRouter, File, UploadFile, HTTPException
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict
from typing import List
import uuid
from datetime import datetime, timezone
import PyPDF2
import io
import google.generativeai as genai
from contextlib import asynccontextmanager

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# Initialize Google Gemini client
gemini_api_key = os.environ.get('GEMINI_API_KEY')
if gemini_api_key:
    genai.configure(api_key=gemini_api_key)

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    yield
    # Shutdown
    client.close()

app = FastAPI(lifespan=lifespan)

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Define Models
class SectionSummary(BaseModel):
    section_number: int
    content: str

class DocumentSummary(BaseModel):
    model_config = ConfigDict(extra="ignore")
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    filename: str
    file_size: int
    file_type: str
    sections: List[SectionSummary]
    overall_summary: str
    upload_timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

# Helper function to extract text from PDF
def extract_text_from_pdf(file_content: bytes) -> str:
    try:
        pdf_file = io.BytesIO(file_content)
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text()
        return text
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error extracting text from PDF: {str(e)}")

# Helper function to extract text from TXT
def extract_text_from_txt(file_content: bytes) -> str:
    try:
        return file_content.decode('utf-8')
    except UnicodeDecodeError:
        try:
            return file_content.decode('latin-1')
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Error reading text file: {str(e)}")

# Helper function to chunk text
def chunk_text(text: str, chunk_size: int = 3500) -> List[str]:
    """Split text into chunks based on size, preserving paragraph structure"""
    paragraphs = text.split('\n\n')
    chunks = []
    current_chunk = ""
    
    for para in paragraphs:
        if len(current_chunk) + len(para) <= chunk_size:
            current_chunk += para + "\n\n"
        else:
            if current_chunk:
                chunks.append(current_chunk.strip())
            current_chunk = para + "\n\n"
    
    if current_chunk:
        chunks.append(current_chunk.strip())
    
    return chunks if chunks else [text]

# Helper function to summarize with LLM
async def summarize_text(text: str, summary_type: str = "section") -> str:
    try:
        api_key = os.environ.get('GEMINI_API_KEY')
        if not api_key:
            logger.error("GEMINI_API_KEY not configured")
            raise HTTPException(status_code=500, detail="GEMINI_API_KEY not configured")
        
        if summary_type == "section":
            prompt = f"Provide a concise summary of the following text section in 3-4 sentences, highlighting the main points:\n\n{text}"
        else:
            prompt = f"Based on all the section summaries provided, create a comprehensive overall summary of the entire document in 5-6 sentences:\n\n{text}"
        
        logger.info(f"Calling Gemini API with prompt length: {len(prompt)}")
        # Use a supported Gemini model available to the current API key
        # "gemini-2.5-flash" is available and supports generateContent
        model = genai.GenerativeModel('gemini-2.5-flash')
        response = model.generate_content(prompt)
        
        if not response or not response.text:
            logger.error("Empty response from Gemini API")
            raise HTTPException(status_code=500, detail="Empty response from Gemini API")
        
        logger.info(f"Gemini response received: {len(response.text)} characters")
        return response.text
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in summarize_text: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error summarizing text: {str(e)}")

@api_router.get("/")
async def root():
    return {"message": "AI Document Summarizer API"}

@api_router.post("/summarize", response_model=DocumentSummary)
async def summarize_document(file: UploadFile = File(...)):
    try:
        logger.info(f"Received file: {file.filename}")
        
        # Validate file type
        if not file.filename.lower().endswith(('.pdf', '.txt')):
            raise HTTPException(status_code=400, detail="Only PDF and TXT files are supported")
        
        # Read file content
        file_content = await file.read()
        file_size = len(file_content)
        logger.info(f"File size: {file_size} bytes")
        
        # Validate file size (10MB limit)
        max_size = 10 * 1024 * 1024  # 10MB in bytes
        if file_size > max_size:
            raise HTTPException(status_code=400, detail="File size exceeds 10MB limit")
        
        # Validate minimum size (at least 10 bytes)
        if file_size < 10:
            raise HTTPException(status_code=400, detail="File is too small or empty")
        
        # Extract text based on file type
        file_type = file.filename.lower().split('.')[-1]
        if file_type == 'pdf':
            text = extract_text_from_pdf(file_content)
        else:
            text = extract_text_from_txt(file_content)
        
        logger.info(f"Extracted text length: {len(text)} characters")
        
        if not text.strip():
            raise HTTPException(status_code=400, detail="No text content found in the file")
        
        # Chunk the text
        chunks = chunk_text(text)
        logger.info(f"Created {len(chunks)} chunks")
        
        # Generate section summaries
        section_summaries = []
        for i, chunk in enumerate(chunks, 1):
            logger.info(f"Processing chunk {i}/{len(chunks)}")
            summary = await summarize_text(chunk, "section")
            section_summaries.append(SectionSummary(
                section_number=i,
                content=summary
            ))
        
        # Generate overall summary
        all_summaries_text = "\n\n".join([f"Section {s.section_number}: {s.content}" for s in section_summaries])
        logger.info("Generating overall summary")
        overall_summary = await summarize_text(all_summaries_text, "overall")
    
        # Create document summary object
        doc_summary = DocumentSummary(
            filename=file.filename,
            file_size=file_size,
            file_type=file_type,
            sections=section_summaries,
            overall_summary=overall_summary
        )
        
        # Store in database
        doc = doc_summary.model_dump()
        doc['upload_timestamp'] = doc['upload_timestamp'].isoformat()
        doc['sections'] = [s.dict() for s in section_summaries]
        await db.document_summaries.insert_one(doc)
        
        logger.info(f"Successfully processed file: {file.filename}")
        return doc_summary
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing document: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error processing document: {str(e)}")

@api_router.get("/summaries", response_model=List[DocumentSummary])
async def get_summaries():
    summaries = await db.document_summaries.find({}, {"_id": 0}).sort("upload_timestamp", -1).to_list(100)
    
    for summary in summaries:
        if isinstance(summary['upload_timestamp'], str):
            summary['upload_timestamp'] = datetime.fromisoformat(summary['upload_timestamp'])
    
    return summaries

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
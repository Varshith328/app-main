import { useState } from "react";
import axios from "axios";
import { toast } from "sonner";
import { FileText, Upload, Loader2, ChevronDown, ChevronUp, Sparkles } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const HomePage = () => {
  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [summary, setSummary] = useState(null);
  const [dragActive, setDragActive] = useState(false);
  const [expandedSections, setExpandedSections] = useState(new Set());

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    const droppedFile = e.dataTransfer.files[0];
    if (droppedFile) {
      validateAndSetFile(droppedFile);
    }
  };

  const handleFileChange = (e) => {
    const selectedFile = e.target.files[0];
    if (selectedFile) {
      validateAndSetFile(selectedFile);
    }
  };

  const validateAndSetFile = (selectedFile) => {
    // Validate file type
    const validTypes = ['application/pdf', 'text/plain'];
    if (!validTypes.includes(selectedFile.type)) {
      toast.error("Invalid file type. Please upload a PDF or TXT file.");
      return;
    }

    // Validate file size (10MB)
    const maxSize = 10 * 1024 * 1024;
    if (selectedFile.size > maxSize) {
      toast.error("File size exceeds 10MB limit.");
      return;
    }

    setFile(selectedFile);
    setSummary(null);
    toast.success(`File "${selectedFile.name}" selected successfully!`);
  };

  const handleSubmit = async () => {
    if (!file) {
      toast.error("Please select a file first.");
      return;
    }

    setLoading(true);
    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await axios.post(`${API}/summarize`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
        timeout: 120000, // 2 minute timeout
      });

      setSummary(response.data);
      toast.success("Document summarized successfully!");
      
      // Scroll to results
      setTimeout(() => {
        const resultsElement = document.querySelector('[data-testid="summary-results"]');
        if (resultsElement) {
          resultsElement.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }
      }, 100);
    } catch (error) {
      console.error('Error summarizing document:', error);
      
      let errorMsg = "Failed to summarize document. Please try again.";
      
      if (error.code === 'ECONNABORTED') {
        errorMsg = "Request timed out. The document may be too large. Please try a smaller file.";
      } else if (error.response) {
        errorMsg = error.response.data?.detail || errorMsg;
        console.error('Server response:', error.response.status, error.response.data);
      } else if (error.request) {
        errorMsg = "No response from server. Please check your connection.";
      }
      
      toast.error(errorMsg);
    } finally {
      setLoading(false);
    }
  };

  const toggleSection = (sectionNum) => {
    setExpandedSections(prev => {
      const newSet = new Set(prev);
      if (newSet.has(sectionNum)) {
        newSet.delete(sectionNum);
      } else {
        newSet.add(sectionNum);
      }
      return newSet;
    });
  };

  const formatFileSize = (bytes) => {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(2) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(2) + ' MB';
  };

  return (
    <div className="min-h-screen relative">
      {/* Hero glow background */}
      <div className="absolute top-0 left-1/2 -translate-x-1/2 w-full h-96 bg-[radial-gradient(circle_at_50%_0%,rgba(99,102,241,0.15)_0%,transparent_50%)] pointer-events-none" />
      
      {/* Hero background image */}
      <div 
        className="absolute top-0 left-0 w-full h-96 opacity-20 pointer-events-none"
        style={{
          backgroundImage: 'url(https://images.unsplash.com/photo-1746470427657-eb0b0115455f?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NTY2NzF8MHwxfHNlYXJjaHwxfHxhYnN0cmFjdCUyMGRpZ2l0YWwlMjBuZXR3b3JrJTIwYmx1ZXxlbnwwfHx8fDE3NjUwMzExNDF8MA&ixlib=rb-4.1.0&q=85)',
          backgroundSize: 'cover',
          backgroundPosition: 'center',
          maskImage: 'linear-gradient(to bottom, rgba(0,0,0,1) 0%, rgba(0,0,0,0) 100%)',
          WebkitMaskImage: 'linear-gradient(to bottom, rgba(0,0,0,1) 0%, rgba(0,0,0,0) 100%)',
        }}
      />

      <div className="relative max-w-6xl mx-auto px-6 py-16">
        {/* Header */}
        <div className="text-center mb-16 space-y-4">
          <div className="inline-flex items-center gap-2 px-4 py-2 bg-primary/10 border border-primary/20 rounded-full mb-4">
            <Sparkles className="w-4 h-4 text-accent" />
            <span className="text-sm font-mono text-accent">AI-Powered Summarization</span>
          </div>
          <h1 className="text-4xl sm:text-5xl lg:text-6xl font-heading font-bold text-foreground">
            Document Summarizer
          </h1>
          <p className="text-lg text-muted-foreground max-w-2xl mx-auto">
            Upload your PDF or TXT files and get intelligent, section-wise summaries powered by advanced AI
          </p>
        </div>

        {/* Upload Section */}
        <Card className="bg-zinc-900/60 backdrop-blur-xl border-white/10 shadow-deep p-8 mb-8">
          <div
            data-testid="upload-zone"
            className={`relative border-2 border-dashed rounded-lg p-12 text-center transition-all duration-300 ${
              dragActive
                ? 'border-accent bg-accent/5'
                : 'border-zinc-800 hover:border-zinc-700'
            }`}
            onDragEnter={handleDrag}
            onDragLeave={handleDrag}
            onDragOver={handleDrag}
            onDrop={handleDrop}
          >
            <input
              type="file"
              id="file-upload"
              data-testid="file-input"
              className="hidden"
              accept=".pdf,.txt"
              onChange={handleFileChange}
            />
            
            <div className="space-y-4">
              <div className="flex justify-center">
                <div className={`p-4 rounded-full bg-primary/10 ${
                  dragActive ? 'tracing-beam' : ''
                }`}>
                  <FileText className="w-12 h-12 text-primary" />
                </div>
              </div>
              
              <div>
                <h3 className="text-xl font-heading font-semibold text-foreground mb-2">
                  {file ? file.name : 'Drop your document here'}
                </h3>
                <p className="text-muted-foreground mb-4">
                  {file ? (
                    <span className="font-mono text-sm">
                      {formatFileSize(file.size)} • {file.type.includes('pdf') ? 'PDF' : 'TXT'}
                    </span>
                  ) : (
                    'or click to browse'
                  )}
                </p>
              </div>

              <div className="flex items-center justify-center gap-3">
                <Button
                  data-testid="browse-button"
                  variant="outline"
                  onClick={() => document.getElementById('file-upload').click()}
                  className="bg-zinc-900/50 border-zinc-800 hover:bg-zinc-800 hover:border-zinc-700"
                >
                  <Upload className="w-4 h-4 mr-2" />
                  Browse Files
                </Button>
                
                {file && (
                  <Button
                    data-testid="summarize-button"
                    onClick={handleSubmit}
                    disabled={loading}
                    className="bg-primary hover:bg-primary/90 text-primary-foreground shadow-glow active:scale-95 transition-transform"
                  >
                    {loading ? (
                      <>
                        <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                        Processing...
                      </>
                    ) : (
                      <>
                        <Sparkles className="w-4 h-4 mr-2" />
                        Summarize
                      </>
                    )}
                  </Button>
                )}
              </div>

              <p className="text-xs text-muted-foreground font-mono">
                Supported formats: PDF, TXT • Max size: 10MB
              </p>
            </div>
          </div>
        </Card>

        {/* Summary Results */}
        {summary && (
          <div data-testid="summary-results" className="space-y-8 fade-in-up">
            {/* Overall Summary */}
            <Card className="bg-zinc-950 border-zinc-800 p-8 shadow-deep">
              <div className="flex items-start gap-4 mb-4">
                <div className="p-3 bg-accent/10 rounded-lg">
                  <Sparkles className="w-6 h-6 text-accent" />
                </div>
                <div className="flex-1">
                  <h2 className="text-2xl font-heading font-bold text-foreground mb-2">
                    Overall Summary
                  </h2>
                  <div className="flex items-center gap-4 text-sm text-muted-foreground font-mono">
                    <span>{summary.filename}</span>
                    <span>•</span>
                    <span>{summary.sections.length} sections</span>
                    <span>•</span>
                    <span>{formatFileSize(summary.file_size)}</span>
                  </div>
                </div>
              </div>
              <p data-testid="overall-summary" className="text-foreground leading-relaxed text-base">
                {summary.overall_summary}
              </p>
            </Card>

            {/* Section Summaries */}
            <div>
              <h3 className="text-xl font-heading font-semibold text-foreground mb-4 flex items-center gap-2">
                <FileText className="w-5 h-5 text-primary" />
                Section-wise Breakdown
              </h3>
              <div className="space-y-4 stagger-children">
                {summary.sections.map((section) => (
                  <Card
                    key={section.section_number}
                    data-testid={`section-${section.section_number}`}
                    className="bg-zinc-900/60 backdrop-blur-xl border-white/10 hover:border-white/20 transition-all duration-300 overflow-hidden"
                  >
                    <button
                      data-testid={`section-toggle-${section.section_number}`}
                      onClick={() => toggleSection(section.section_number)}
                      className="w-full p-6 text-left flex items-center justify-between hover:bg-white/5 transition-colors"
                    >
                      <div className="flex items-center gap-4">
                        <div className="px-3 py-1 bg-primary/10 border border-primary/20 rounded-md">
                          <span className="text-sm font-mono font-semibold text-primary">
                            Section {section.section_number}
                          </span>
                        </div>
                      </div>
                      {expandedSections.has(section.section_number) ? (
                        <ChevronUp className="w-5 h-5 text-muted-foreground" />
                      ) : (
                        <ChevronDown className="w-5 h-5 text-muted-foreground" />
                      )}
                    </button>
                    
                    {expandedSections.has(section.section_number) && (
                      <div className="px-6 pb-6 pt-0">
                        <div className="pl-4 border-l-2 border-primary/30">
                          <p data-testid={`section-content-${section.section_number}`} className="text-foreground leading-relaxed">
                            {section.content}
                          </p>
                        </div>
                      </div>
                    )}
                  </Card>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* Loading State */}
        {loading && (
          <Card className="bg-zinc-900/60 backdrop-blur-xl border-white/10 p-8 text-center">
            <Loader2 className="w-12 h-12 text-primary animate-spin mx-auto mb-4" />
            <h3 className="text-xl font-heading font-semibold text-foreground mb-2">
              Processing Document
            </h3>
            <p className="text-muted-foreground">
              Analyzing content and generating summaries...
            </p>
          </Card>
        )}
      </div>
    </div>
  );
};

export default HomePage;
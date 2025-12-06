import requests
import sys
import os
import io
from datetime import datetime

class DocumentSummarizerTester:
    def __init__(self, base_url="https://smartsumm.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []

    def log_test(self, name, success, details=""):
        """Log test result"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name} - PASSED")
        else:
            print(f"❌ {name} - FAILED: {details}")
        
        self.test_results.append({
            "test": name,
            "success": success,
            "details": details
        })

    def test_api_root(self):
        """Test API root endpoint"""
        try:
            response = requests.get(f"{self.api_url}/", timeout=10)
            success = response.status_code == 200
            details = f"Status: {response.status_code}"
            if success:
                data = response.json()
                details += f", Response: {data}"
            self.log_test("API Root Endpoint", success, details)
            return success
        except Exception as e:
            self.log_test("API Root Endpoint", False, str(e))
            return False

    def test_file_upload_validation(self):
        """Test file upload with invalid file types"""
        try:
            # Test invalid file type
            files = {'file': ('test.jpg', b'fake image content', 'image/jpeg')}
            response = requests.post(f"{self.api_url}/summarize", files=files, timeout=30)
            
            success = response.status_code == 400
            details = f"Status: {response.status_code}"
            if response.status_code == 400:
                error_data = response.json()
                details += f", Error: {error_data.get('detail', 'No detail')}"
            
            self.log_test("File Type Validation (Invalid)", success, details)
            return success
        except Exception as e:
            self.log_test("File Type Validation (Invalid)", False, str(e))
            return False

    def test_file_size_validation(self):
        """Test file upload with oversized file"""
        try:
            # Create a file larger than 10MB
            large_content = b'x' * (11 * 1024 * 1024)  # 11MB
            files = {'file': ('large_test.txt', large_content, 'text/plain')}
            response = requests.post(f"{self.api_url}/summarize", files=files, timeout=30)
            
            success = response.status_code == 400
            details = f"Status: {response.status_code}"
            if response.status_code == 400:
                error_data = response.json()
                details += f", Error: {error_data.get('detail', 'No detail')}"
            
            self.log_test("File Size Validation (>10MB)", success, details)
            return success
        except Exception as e:
            self.log_test("File Size Validation (>10MB)", False, str(e))
            return False

    def test_txt_file_summarization(self):
        """Test TXT file summarization"""
        try:
            # Create a sample TXT file
            txt_content = """
            Artificial Intelligence and Machine Learning

            Artificial Intelligence (AI) is a rapidly evolving field that focuses on creating intelligent machines capable of performing tasks that typically require human intelligence. These tasks include learning, reasoning, problem-solving, perception, and language understanding.

            Machine Learning Applications

            Machine learning, a subset of AI, has found applications in various domains including healthcare, finance, transportation, and entertainment. In healthcare, ML algorithms help in disease diagnosis and drug discovery. In finance, they are used for fraud detection and algorithmic trading.

            Future Prospects

            The future of AI looks promising with advancements in deep learning, neural networks, and quantum computing. However, ethical considerations and responsible AI development remain crucial challenges that need to be addressed.
            """
            
            files = {'file': ('test_document.txt', txt_content.encode('utf-8'), 'text/plain')}
            response = requests.post(f"{self.api_url}/summarize", files=files, timeout=60)
            
            success = response.status_code == 200
            details = f"Status: {response.status_code}"
            
            if success:
                data = response.json()
                # Validate response structure
                required_fields = ['id', 'filename', 'file_size', 'file_type', 'sections', 'overall_summary']
                missing_fields = [field for field in required_fields if field not in data]
                
                if missing_fields:
                    success = False
                    details += f", Missing fields: {missing_fields}"
                else:
                    details += f", Sections: {len(data['sections'])}, Overall summary length: {len(data['overall_summary'])}"
                    # Check if sections have content
                    if not data['sections'] or not data['overall_summary']:
                        success = False
                        details += ", Empty sections or overall summary"
            else:
                try:
                    error_data = response.json()
                    details += f", Error: {error_data.get('detail', 'No detail')}"
                except:
                    details += f", Response: {response.text[:200]}"
            
            self.log_test("TXT File Summarization", success, details)
            return success, data if success else None
        except Exception as e:
            self.log_test("TXT File Summarization", False, str(e))
            return False, None

    def test_get_summaries(self):
        """Test getting all summaries"""
        try:
            response = requests.get(f"{self.api_url}/summaries", timeout=30)
            success = response.status_code == 200
            details = f"Status: {response.status_code}"
            
            if success:
                data = response.json()
                details += f", Number of summaries: {len(data)}"
                if isinstance(data, list):
                    details += ", Response is valid list"
                else:
                    success = False
                    details += ", Response is not a list"
            else:
                try:
                    error_data = response.json()
                    details += f", Error: {error_data.get('detail', 'No detail')}"
                except:
                    details += f", Response: {response.text[:200]}"
            
            self.log_test("Get Summaries Endpoint", success, details)
            return success
        except Exception as e:
            self.log_test("Get Summaries Endpoint", False, str(e))
            return False

    def test_empty_file(self):
        """Test empty file handling"""
        try:
            files = {'file': ('empty.txt', b'', 'text/plain')}
            response = requests.post(f"{self.api_url}/summarize", files=files, timeout=30)
            
            success = response.status_code == 400
            details = f"Status: {response.status_code}"
            if response.status_code == 400:
                error_data = response.json()
                details += f", Error: {error_data.get('detail', 'No detail')}"
            
            self.log_test("Empty File Handling", success, details)
            return success
        except Exception as e:
            self.log_test("Empty File Handling", False, str(e))
            return False

    def run_all_tests(self):
        """Run all backend tests"""
        print("🚀 Starting AI Document Summarizer Backend Tests")
        print(f"Testing API at: {self.api_url}")
        print("=" * 60)

        # Test API availability
        if not self.test_api_root():
            print("❌ API is not accessible. Stopping tests.")
            return False

        # Test file validations
        self.test_file_upload_validation()
        self.test_file_size_validation()
        self.test_empty_file()

        # Test core functionality
        success, summary_data = self.test_txt_file_summarization()
        
        # Test get summaries
        self.test_get_summaries()

        # Print summary
        print("\n" + "=" * 60)
        print(f"📊 Test Results: {self.tests_passed}/{self.tests_run} tests passed")
        print(f"Success Rate: {(self.tests_passed/self.tests_run)*100:.1f}%")
        
        if self.tests_passed < self.tests_run:
            print("\n❌ Failed Tests:")
            for result in self.test_results:
                if not result['success']:
                    print(f"  - {result['test']}: {result['details']}")

        return self.tests_passed == self.tests_run

def main():
    tester = DocumentSummarizerTester()
    success = tester.run_all_tests()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
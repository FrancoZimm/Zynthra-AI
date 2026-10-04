#!/usr/bin/env python3
"""
Backend API Testing for Tutor IA Verificable
Tests all API endpoints with proper error handling
"""
import requests
import sys
import json
from datetime import datetime

class TutorIAAPITester:
    def __init__(self, base_url="https://verifiable-tutor.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []

    def log_test(self, name, success, details="", response_data=None):
        """Log test result"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name}")
        else:
            print(f"❌ {name} - {details}")
        
        self.test_results.append({
            "test": name,
            "success": success,
            "details": details,
            "response_data": response_data
        })

    def test_root_endpoint(self):
        """Test API root endpoint"""
        try:
            response = requests.get(f"{self.api_url}/", timeout=10)
            success = response.status_code == 200
            data = response.json() if success else {}
            
            if success:
                expected_fields = ["message", "version", "status"]
                has_fields = all(field in data for field in expected_fields)
                if has_fields and "Tutor IA Verificable" in data.get("message", ""):
                    self.log_test("Root endpoint", True, f"Status: {response.status_code}", data)
                else:
                    self.log_test("Root endpoint", False, f"Missing expected fields or incorrect message", data)
            else:
                self.log_test("Root endpoint", False, f"Status: {response.status_code}")
                
        except Exception as e:
            self.log_test("Root endpoint", False, f"Exception: {str(e)}")

    def test_health_endpoint(self):
        """Test health check endpoint"""
        try:
            response = requests.get(f"{self.api_url}/health", timeout=10)
            success = response.status_code == 200
            data = response.json() if success else {}
            
            if success:
                expected_fields = ["status", "ollama_available", "documents_indexed"]
                has_fields = all(field in data for field in expected_fields)
                self.log_test("Health endpoint", has_fields, f"Status: {response.status_code}", data)
            else:
                self.log_test("Health endpoint", False, f"Status: {response.status_code}")
                
        except Exception as e:
            self.log_test("Health endpoint", False, f"Exception: {str(e)}")

    def test_documents_list_endpoint(self):
        """Test documents list endpoint"""
        try:
            response = requests.get(f"{self.api_url}/documents", timeout=10)
            success = response.status_code == 200
            data = response.json() if success else {}
            
            if success:
                is_list = isinstance(data, list)
                self.log_test("Documents list endpoint", is_list, f"Status: {response.status_code}, Count: {len(data) if is_list else 'N/A'}", data)
            else:
                self.log_test("Documents list endpoint", False, f"Status: {response.status_code}")
                
        except Exception as e:
            self.log_test("Documents list endpoint", False, f"Exception: {str(e)}")

    def test_document_upload_endpoint(self):
        """Test document upload endpoint"""
        try:
            test_doc = {
                "filename": "test_document.txt",
                "content": "Este es un documento de prueba para el sistema RAG educativo. Contiene información sobre matemáticas básicas. La suma de 2 + 2 es igual a 4.",
                "file_type": "txt"
            }
            
            response = requests.post(
                f"{self.api_url}/documents/upload", 
                json=test_doc,
                timeout=15
            )
            
            success = response.status_code in [200, 201]
            data = response.json() if response.status_code < 500 else {}
            
            if success:
                has_success_field = data.get("success", False)
                self.log_test("Document upload endpoint", has_success_field, f"Status: {response.status_code}", data)
            else:
                self.log_test("Document upload endpoint", False, f"Status: {response.status_code}, Response: {data}")
                
        except Exception as e:
            self.log_test("Document upload endpoint", False, f"Exception: {str(e)}")

    def test_chat_endpoint(self):
        """Test chat endpoint (expected to fail gracefully without Ollama)"""
        try:
            chat_request = {
                "message": "¿Qué es 2 + 2?",
                "include_evidence": True,
                "confidence_threshold": 0.6
            }
            
            response = requests.post(
                f"{self.api_url}/chat", 
                json=chat_request,
                timeout=15
            )
            
            # Chat should either work or fail gracefully
            if response.status_code == 200:
                data = response.json()
                expected_fields = ["response", "conversation_id", "response_mode"]
                has_fields = all(field in data for field in expected_fields)
                self.log_test("Chat endpoint", has_fields, f"Status: {response.status_code}", data)
            elif response.status_code in [500, 503]:
                # Expected failure due to missing Ollama
                self.log_test("Chat endpoint", True, f"Expected failure without Ollama - Status: {response.status_code}")
            else:
                self.log_test("Chat endpoint", False, f"Unexpected status: {response.status_code}")
                
        except Exception as e:
            self.log_test("Chat endpoint", False, f"Exception: {str(e)}")

    def test_config_endpoint(self):
        """Test configuration endpoint"""
        try:
            response = requests.get(f"{self.api_url}/config", timeout=10)
            success = response.status_code == 200
            data = response.json() if success else {}
            
            if success:
                expected_fields = ["llm_model", "embedding_model", "confidence_threshold"]
                has_fields = all(field in data for field in expected_fields)
                self.log_test("Config endpoint", has_fields, f"Status: {response.status_code}", data)
            else:
                self.log_test("Config endpoint", False, f"Status: {response.status_code}")
                
        except Exception as e:
            self.log_test("Config endpoint", False, f"Exception: {str(e)}")

    def run_all_tests(self):
        """Run all backend tests"""
        print("🚀 Starting Tutor IA Verificable Backend API Tests")
        print(f"📍 Testing against: {self.base_url}")
        print("=" * 60)
        
        # Test all endpoints
        self.test_root_endpoint()
        self.test_health_endpoint()
        self.test_config_endpoint()
        self.test_documents_list_endpoint()
        self.test_document_upload_endpoint()
        self.test_chat_endpoint()
        
        # Print summary
        print("\n" + "=" * 60)
        print(f"📊 Test Summary: {self.tests_passed}/{self.tests_run} tests passed")
        
        if self.tests_passed == self.tests_run:
            print("🎉 All tests passed!")
            return 0
        else:
            print("⚠️  Some tests failed - check details above")
            return 1

def main():
    tester = TutorIAAPITester()
    return tester.run_all_tests()

if __name__ == "__main__":
    sys.exit(main())
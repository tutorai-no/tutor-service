#!/usr/bin/env python
"""
Comprehensive API endpoint test script for Aksio Backend
Tests all major endpoints to ensure they're working correctly.
"""

import requests
import json
import sys
from datetime import datetime

# API base URL
BASE_URL = "http://localhost:8000/api/v1"

class APITester:
    def __init__(self, base_url=BASE_URL):
        self.base_url = base_url
        self.session = requests.Session()
        self.access_token = None
        self.user_id = None
        self.course_id = None
        self.flashcard_id = None
        self.quiz_id = None
        
    def log(self, message, level="INFO"):
        """Log test messages"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {level}: {message}")
    
    def test_health_check(self):
        """Test health check endpoint"""
        self.log("Testing health check endpoint...")
        try:
            response = self.session.get(f"{self.base_url}/../health/")
            assert response.status_code == 200
            assert response.json()["status"] == "healthy"
            self.log("PASS Health check passed")
            return True
        except Exception as e:
            self.log(f"FAIL Health check failed: {e}", "ERROR")
            return False
    
    def test_user_registration(self):
        """Test user registration"""
        self.log("Testing user registration...")
        try:
            data = {
                "username": f"testuser_{datetime.now().timestamp()}",
                "email": f"test_{datetime.now().timestamp()}@example.com",
                "password": "testpassword123",
                "password_confirm": "testpassword123",
                "first_name": "Test",
                "last_name": "User"
            }
            
            response = self.session.post(f"{self.base_url}/accounts/register/", json=data)
            
            if response.status_code == 201:
                self.log("PASS User registration successful")
                return True
            else:
                self.log(f"FAIL User registration failed: {response.status_code} - {response.text}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"FAIL User registration error: {e}", "ERROR")
            return False
    
    def test_user_login(self):
        """Test user login and JWT token retrieval"""
        self.log("Testing user login...")
        try:
            # First create a user for login
            timestamp = datetime.now().timestamp()
            username = f"logintest_{timestamp}"
            email = f"logintest_{timestamp}@example.com"
            password = "testpassword123"
            
            # Register user
            reg_data = {
                "username": username,
                "email": email,
                "password": password,
                "password_confirm": password,
                "first_name": "Login",
                "last_name": "Test"
            }
            self.session.post(f"{self.base_url}/accounts/register/", json=reg_data)
            
            # Login
            login_data = {
                "username": username,
                "password": password
            }
            
            response = self.session.post(f"{self.base_url}/accounts/login/", json=login_data)
            
            if response.status_code == 200:
                data = response.json()
                self.access_token = data.get("access")
                self.user_id = data.get("user", {}).get("id")
                
                # Set authorization header for future requests
                self.session.headers.update({
                    "Authorization": f"Bearer {self.access_token}"
                })
                
                self.log("PASS User login successful")
                return True
            else:
                self.log(f"FAIL User login failed: {response.status_code} - {response.text}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"FAIL User login error: {e}", "ERROR")
            return False
    
    def test_course_operations(self):
        """Test course CRUD operations"""
        self.log("Testing course operations...")
        try:
            # Create course
            course_data = {
                "name": f"Test Course {datetime.now().timestamp()}",
                "description": "A test course for API testing",
                "difficulty_level": 3,
                "language": "en"
            }
            
            response = self.session.post(f"{self.base_url}/courses/courses/", json=course_data)
            
            if response.status_code == 201:
                self.course_id = response.json()["id"]
                self.log("PASS Course creation successful")
                
                # Test course listing
                list_response = self.session.get(f"{self.base_url}/courses/courses/")
                if list_response.status_code == 200:
                    self.log("PASS Course listing successful")
                    
                    # Test course detail
                    detail_response = self.session.get(f"{self.base_url}/courses/courses/{self.course_id}/")
                    if detail_response.status_code == 200:
                        self.log("PASS Course detail retrieval successful")
                        return True
                    else:
                        self.log("FAIL Course detail retrieval failed", "ERROR")
                        return False
                else:
                    self.log("FAIL Course listing failed", "ERROR")
                    return False
            else:
                self.log(f"FAIL Course creation failed: {response.status_code} - {response.text}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"FAIL Course operations error: {e}", "ERROR")
            return False
    
    def test_flashcard_operations(self):
        """Test flashcard CRUD operations"""
        self.log("Testing flashcard operations...")
        try:
            if not self.course_id:
                self.log("FAIL No course available for flashcard testing", "ERROR")
                return False
            
            # Create flashcard
            flashcard_data = {
                "course": self.course_id,
                "question": "What is the capital of France?",
                "answer": "Paris",
                "difficulty_level": "medium"
            }
            
            response = self.session.post(f"{self.base_url}/assessments/flashcards/", json=flashcard_data)
            
            if response.status_code == 201:
                self.flashcard_id = response.json()["id"]
                self.log("PASS Flashcard creation successful")
                
                # Test flashcard listing
                list_response = self.session.get(f"{self.base_url}/assessments/flashcards/")
                if list_response.status_code == 200:
                    self.log("PASS Flashcard listing successful")
                    
                    # Test flashcard stats
                    stats_response = self.session.get(f"{self.base_url}/assessments/flashcards/stats/")
                    if stats_response.status_code == 200:
                        self.log("PASS Flashcard stats retrieval successful")
                        return True
                    else:
                        self.log("FAIL Flashcard stats retrieval failed", "ERROR")
                        return False
                else:
                    self.log("FAIL Flashcard listing failed", "ERROR")
                    return False
            else:
                self.log(f"FAIL Flashcard creation failed: {response.status_code} - {response.text}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"FAIL Flashcard operations error: {e}", "ERROR")
            return False
    
    def test_quiz_operations(self):
        """Test quiz operations"""
        self.log("Testing quiz operations...")
        try:
            if not self.course_id:
                self.log("FAIL No course available for quiz testing", "ERROR")
                return False
            
            # Create quiz
            quiz_data = {
                "course": self.course_id,
                "title": f"Test Quiz {datetime.now().timestamp()}",
                "description": "A test quiz for API testing",
                "quiz_type": "practice",
                "status": "published"
            }
            
            response = self.session.post(f"{self.base_url}/assessments/quizzes/", json=quiz_data)
            
            if response.status_code == 201:
                self.quiz_id = response.json()["id"]
                self.log("PASS Quiz creation successful")
                
                # Test quiz listing
                list_response = self.session.get(f"{self.base_url}/assessments/quizzes/")
                if list_response.status_code == 200:
                    self.log("PASS Quiz listing successful")
                    return True
                else:
                    self.log("FAIL Quiz listing failed", "ERROR")
                    return False
            else:
                self.log(f"FAIL Quiz creation failed: {response.status_code} - {response.text}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"FAIL Quiz operations error: {e}", "ERROR")
            return False
    
    def test_chat_operations(self):
        """Test chat operations"""
        self.log("Testing chat operations...")
        try:
            if not self.course_id:
                self.log("FAIL No course available for chat testing", "ERROR")
                return False
            
            # Create chat
            chat_data = {
                "course": self.course_id,
                "title": f"Test Chat {datetime.now().timestamp()}"
            }
            
            response = self.session.post(f"{self.base_url}/chat/chats/", json=chat_data)
            
            if response.status_code == 201:
                chat_id = response.json()["id"]
                self.log("PASS Chat creation successful")
                
                # Test chat listing
                list_response = self.session.get(f"{self.base_url}/chat/chats/")
                if list_response.status_code == 200:
                    self.log("PASS Chat listing successful")
                    return True
                else:
                    self.log("FAIL Chat listing failed", "ERROR")
                    return False
            else:
                self.log(f"FAIL Chat creation failed: {response.status_code} - {response.text}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"FAIL Chat operations error: {e}", "ERROR")
            return False
    
    def run_all_tests(self):
        """Run all API tests"""
        self.log("Starting comprehensive API endpoint tests...")
        self.log("=" * 50)
        
        tests = [
            ("Health Check", self.test_health_check),
            ("User Registration", self.test_user_registration),
            ("User Login", self.test_user_login),
            ("Course Operations", self.test_course_operations),
            ("Flashcard Operations", self.test_flashcard_operations),
            ("Quiz Operations", self.test_quiz_operations),
            ("Chat Operations", self.test_chat_operations),
        ]
        
        passed = 0
        total = len(tests)
        
        for test_name, test_func in tests:
            self.log(f"\n--- {test_name} ---")
            if test_func():
                passed += 1
            else:
                self.log(f"Test '{test_name}' failed", "ERROR")
        
        self.log("=" * 50)
        self.log(f"Test Results: {passed}/{total} tests passed")
        
        if passed == total:
            self.log("SUCCESS All tests passed!", "SUCCESS")
            return True
        else:
            self.log(f"WARNING  {total - passed} tests failed", "WARNING")
            return False

def main():
    """Main function to run API tests"""
    print("Aksio Backend API Endpoint Tester")
    print("=" * 40)
    
    tester = APITester()
    success = tester.run_all_tests()
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
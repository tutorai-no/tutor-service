#!/usr/bin/env python
"""Debug script for chat creation error"""

import requests
import json
from datetime import datetime

# API base URL
BASE_URL = "http://localhost:8000/api/v1"

# Login and get token
login_data = {
    "username": f"testuser_{datetime.now().timestamp()}",
    "email": f"test_{datetime.now().timestamp()}@example.com",
    "password": "testpassword123",
}

# Register first
reg_data = {**login_data, "password_confirm": "testpassword123", "first_name": "Test", "last_name": "User"}
reg_response = requests.post(f"{BASE_URL}/accounts/register/", json=reg_data)
print(f"Registration: {reg_response.status_code}")

# Login
login_response = requests.post(f"{BASE_URL}/accounts/login/", json={"username": login_data["username"], "password": login_data["password"]})
print(f"Login: {login_response.status_code}")

if login_response.status_code == 200:
    token = login_response.json()["access"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # Create a course first
    course_data = {"name": "Test Course", "description": "Test"}
    course_response = requests.post(f"{BASE_URL}/courses/", json=course_data, headers=headers)
    print(f"Course creation: {course_response.status_code}")
    
    if course_response.status_code == 201:
        course_id = course_response.json()["id"]
        
        # Try creating a chat
        chat_data = {
            "title": "Test Chat",
            "course": course_id
        }
        
        print(f"Sending chat data: {json.dumps(chat_data, indent=2)}")
        
        chat_response = requests.post(f"{BASE_URL}/chat/chats/", json=chat_data, headers=headers)
        print(f"\nChat creation status: {chat_response.status_code}")
        
        if chat_response.status_code != 201:
            print(f"Error response: {chat_response.text[:1000]}")
        else:
            print(f"Success: {chat_response.json()}")
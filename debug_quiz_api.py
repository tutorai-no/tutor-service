#!/usr/bin/env python
"""
Debug script for quiz API endpoint
"""

import json
from datetime import datetime

import requests

# API base URL - use internal Docker network
BASE_URL = "http://backend:8000/api/v1"


def debug_quiz_creation():
    """Debug quiz creation through API"""
    session = requests.Session()

    # Step 1: Create and login user
    timestamp = datetime.now().timestamp()
    username = f"quiztest_{timestamp}"
    email = f"quiztest_{timestamp}@example.com"
    password = "testpassword123"

    # Register user
    reg_data = {
        "username": username,
        "email": email,
        "password": password,
        "password_confirm": password,
        "first_name": "Quiz",
        "last_name": "Test",
    }
    reg_response = session.post(f"{BASE_URL}/accounts/register/", json=reg_data)
    print(f"Registration: {reg_response.status_code} - {reg_response.text}")

    # Login
    login_data = {"username": username, "password": password}
    login_response = session.post(f"{BASE_URL}/accounts/login/", json=login_data)
    print(f"Login: {login_response.status_code} - {login_response.text}")

    if login_response.status_code != 200:
        return

    # Set auth header
    token = login_response.json()["access"]
    session.headers.update({"Authorization": f"Bearer {token}"})

    # Step 2: Create course
    course_data = {
        "name": f"Quiz Test Course {timestamp}",
        "description": "A test course for quiz debugging",
        "difficulty_level": 3,
        "language": "en",
    }
    course_response = session.post(f"{BASE_URL}/courses/", json=course_data)
    print(f"Course creation: {course_response.status_code} - {course_response.text}")

    if course_response.status_code != 201:
        return

    course_id = course_response.json()["id"]

    # Step 3: Create quiz
    quiz_data = {
        "course": course_id,
        "title": f"Debug Quiz {timestamp}",
        "description": "A debug quiz",
        "quiz_type": "practice",
        "status": "published",
    }

    print(f"Sending quiz data: {json.dumps(quiz_data, indent=2)}")
    quiz_response = session.post(f"{BASE_URL}/assessments/quizzes/", json=quiz_data)
    print(f"Quiz creation: {quiz_response.status_code}")
    print(f"Response headers: {dict(quiz_response.headers)}")
    print(f"Response text: {quiz_response.text[:1000]}...")  # First 1000 chars


if __name__ == "__main__":
    debug_quiz_creation()

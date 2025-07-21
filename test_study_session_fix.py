import requests
import time
import json

# Base configuration
BASE_URL = "http://localhost:8000/api/v1"

def test_study_session_fix():
    """Test study session creation with minimal setup."""
    print("\n=== Testing Study Session Fix ===\n")
    
    # Step 1: Register user
    print("1. Registering user...")
    user_data = {
        "username": f"test_user_{int(time.time())}",
        "email": f"test_{int(time.time())}@example.com",
        "password": "TestPass123!",
        "password_confirm": "TestPass123!"
    }
    
    response = requests.post(f"{BASE_URL}/accounts/register/", json=user_data)
    if response.status_code == 201:
        print("[OK] User registered")
    else:
        print(f"[FAIL] Registration failed: {response.text}")
        return
    
    # Step 2: Login
    print("\n2. Logging in...")
    login_data = {
        "username": user_data["username"],
        "password": user_data["password"]
    }
    
    response = requests.post(f"{BASE_URL}/accounts/login/", json=login_data)
    if response.status_code == 200:
        print("[OK] Login successful")
        tokens = response.json()
        access_token = tokens["access"]
    else:
        print(f"[FAIL] Login failed: {response.text}")
        return
    
    # Setup headers with auth
    headers = {"Authorization": f"Bearer {access_token}"}
    
    # Step 3: Create course
    print("\n3. Creating course...")
    course_data = {
        "name": "Test Course for Study Sessions",
        "description": "Testing study session functionality",
        "difficulty_level": 2,
        "estimated_hours": 10,
        "is_published": True
    }
    
    response = requests.post(f"{BASE_URL}/courses/", json=course_data, headers=headers)
    if response.status_code == 201:
        print("[OK] Course created")
        course_id = response.json()["id"]
    else:
        print(f"[FAIL] Course creation failed: {response.text}")
        return
    
    # Step 4: Create study session
    print("\n4. Creating study session...")
    session_data = {
        "course": course_id,
        "title": "Test Study Session",
        "description": "Testing the fixed study session endpoint",
        "session_type": "planned",
        "scheduled_start": "2025-01-22T10:00:00Z",
        "scheduled_end": "2025-01-22T11:00:00Z",
        "topics": ["Topic 1", "Topic 2"],
        "materials": ["Material 1"],
        "total_objectives": 2
    }
    
    print(f"Request data: {json.dumps(session_data, indent=2)}")
    
    response = requests.post(f"{BASE_URL}/learning/study-sessions/", json=session_data, headers=headers)
    print(f"\nResponse status: {response.status_code}")
    print(f"Response headers: {dict(response.headers)}")
    
    if response.status_code == 201:
        print("[OK] Study session created successfully!")
        result = response.json()
        print(f"\nResponse data: {json.dumps(result, indent=2)}")
        
        # Check if we got an ID
        session_id = result.get('id')
        if not session_id:
            print("[FAIL] No session ID in response!")
            return
        
        # Step 5: Complete the session
        print("\n5. Completing study session...")
        complete_data = {
            "productivity_rating": 4,
            "notes": "Session completed successfully"
        }
        
        response = requests.post(
            f"{BASE_URL}/learning/study-sessions/{session_id}/complete/", 
            json=complete_data, 
            headers=headers
        )
        
        if response.status_code == 200:
            print("[OK] Study session completed successfully!")
            result = response.json()
            print(f"  Status: {result.get('status')}")
            print(f"  Actual End: {result.get('actual_end')}")
            print(f"  Duration: {result.get('duration_actual')} minutes")
        else:
            print(f"[FAIL] Session completion failed: {response.text}")
            
    else:
        print(f"[FAIL] Study session creation failed!")
        print(f"Response: {response.text}")
        
        # Try to parse error details
        try:
            error_data = response.json()
            print("\nError details:")
            for field, errors in error_data.items():
                print(f"  {field}: {errors}")
        except:
            pass

if __name__ == "__main__":
    test_study_session_fix()
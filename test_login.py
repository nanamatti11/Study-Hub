#!/usr/bin/env python3
import requests
import json

# Test student login with existing user
def test_student_login():
    url = "http://127.0.0.1:5000/api/student/login"
    
    # Test with existing student
    test_data = {
        "username": "Braun23",
        "password": "Student@123"  # This might not be the correct password
    }
    
    print(f"Testing login for: {test_data['username']}")
    
    try:
        response = requests.post(url, 
                               json=test_data,
                               headers={'Content-Type': 'application/json'})
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print("✅ Login successful!")
            else:
                print(f"❌ Login failed: {data.get('message')}")
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    test_student_login()

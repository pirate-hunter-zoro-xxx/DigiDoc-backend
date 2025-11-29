#!/usr/bin/env python3
"""
Comprehensive Test Script for Process Flow API
"""
import requests
import json
from typing import Dict, Optional

BASE_URL = "http://localhost:8000/api/v1"
LEGACY_URL = "http://localhost:8000/api"

# Test results tracking
tests_passed = 0
tests_failed = 0
test_results = []

# Store tokens and IDs for sequential tests
test_data = {
    "user1_token": None,
    "user2_token": None,
    "user3_token": None,
    "user1_id": None,
    "user2_id": None,
    "user3_id": None,
    "request_id": None,
    "stage1_id": None,
    "stage2_id": None,
}


def log_test(test_name: str, passed: bool, details: str = ""):
    """Log test result"""
    global tests_passed, tests_failed
    
    status = "✅ PASS" if passed else "❌ FAIL"
    print(f"{status} | {test_name}")
    
    if details:
        print(f"     └─ {details}")
    
    test_results.append({
        "test": test_name,
        "passed": passed,
        "details": details
    })
    
    if passed:
        tests_passed += 1
    else:
        tests_failed += 1


def test_health_check():
    """Test health check endpoint"""
    try:
        response = requests.get(f"{BASE_URL}/health/health")
        passed = response.status_code == 200 and response.json().get("status") == "healthy"
        log_test("Health Check", passed, f"Status: {response.status_code}")
        return passed
    except Exception as e:
        log_test("Health Check", False, str(e))
        return False


def test_database_health():
    """Test database health check"""
    try:
        response = requests.get(f"{BASE_URL}/health/ready")
        data = response.json()
        passed = response.status_code == 200 and data.get("database") == "connected"
        log_test("Database Health", passed, f"DB Status: {data.get('database')}")
        return passed
    except Exception as e:
        log_test("Database Health", False, str(e))
        return False


def register_user(email: str, password: str, name: str) -> Optional[Dict]:
    """Register a new user"""
    try:
        response = requests.post(
            f"{BASE_URL}/auth/register",
            json={"email": email, "password": password, "name": name}
        )
        
        if response.status_code in [200, 201]:
            data = response.json()
            log_test(f"Register User: {name}", True, f"User ID: {data['user']['id'][:8]}...")
            return data
        else:
            # User might already exist, try login
            response = requests.post(
                f"{BASE_URL}/auth/login",
                json={"email": email, "password": password}
            )
            if response.status_code == 200:
                data = response.json()
                log_test(f"Login Existing User: {name}", True, "Using existing account")
                return data
            else:
                log_test(f"Register/Login User: {name}", False, response.text)
                return None
    except Exception as e:
        log_test(f"Register User: {name}", False, str(e))
        return None


def test_create_request(token: str) -> Optional[str]:
    """Test creating a request with workflow stages"""
    try:
        # Get user IDs for workflow
        if not test_data["user2_id"] or not test_data["user3_id"]:
            log_test("Create Request", False, "Need user2 and user3 IDs for workflow")
            return None
        
        payload = {
            "title": "Test Purchase Request - New Laptop",
            "description": "Need MacBook Pro 16\" M3 for React development work. Current laptop is 4 years old and running slow.",
            "workflow_stages": [
                {
                    "stage_type": "RECOMMEND",
                    "assigned_user_id": test_data["user2_id"],
                    "order_index": 1
                },
                {
                    "stage_type": "APPROVE",
                    "assigned_user_id": test_data["user3_id"],
                    "order_index": 2
                }
            ]
        }
        
        response = requests.post(
            f"{BASE_URL}/requests",
            json=payload,
            headers={"Authorization": f"Bearer {token}"}
        )
        
        if response.status_code in [200, 201]:
            data = response.json()
            request_id = data["id"]
            log_test("Create Request", True, f"Request ID: {request_id[:8]}..., Status: {data['status']}")
            return request_id
        else:
            log_test("Create Request", False, f"Status {response.status_code}: {response.text}")
            return None
    except Exception as e:
        log_test("Create Request", False, str(e))
        return None


def test_list_requests(token: str) -> bool:
    """Test listing requests"""
    try:
        response = requests.get(
            f"{BASE_URL}/requests",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        if response.status_code == 200:
            data = response.json()
            count = len(data.get("requests", []))
            log_test("List Requests", True, f"Found {count} requests")
            return True
        else:
            log_test("List Requests", False, f"Status {response.status_code}")
            return False
    except Exception as e:
        log_test("List Requests", False, str(e))
        return False


def test_get_request_details(token: str, request_id: str) -> bool:
    """Test getting request details"""
    try:
        response = requests.get(
            f"{BASE_URL}/requests/{request_id}",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        if response.status_code == 200:
            data = response.json()
            stages_count = len(data.get("workflow_stages", []))
            log_test("Get Request Details", True, f"Request: {data['title']}, Stages: {stages_count}")
            
            # Store stage IDs for later tests
            if stages_count >= 2:
                test_data["stage1_id"] = data["workflow_stages"][0]["id"]
                test_data["stage2_id"] = data["workflow_stages"][1]["id"]
            
            return True
        else:
            log_test("Get Request Details", False, f"Status {response.status_code}")
            return False
    except Exception as e:
        log_test("Get Request Details", False, str(e))
        return False


def test_update_request(token: str, request_id: str) -> bool:
    """Test updating a request (should work only in DRAFT)"""
    try:
        payload = {
            "description": "Updated description: MacBook Pro 16\" M3 Pro with 36GB RAM"
        }
        
        response = requests.put(
            f"{BASE_URL}/requests/{request_id}",
            json=payload,
            headers={"Authorization": f"Bearer {token}"}
        )
        
        if response.status_code == 200:
            log_test("Update Request (DRAFT)", True, "Successfully updated")
            return True
        else:
            log_test("Update Request (DRAFT)", False, f"Status {response.status_code}")
            return False
    except Exception as e:
        log_test("Update Request (DRAFT)", False, str(e))
        return False


def test_add_comment(token: str, request_id: str) -> bool:
    """Test adding a comment to a request"""
    try:
        payload = {
            "comment": "This is a test comment. When do you need this laptop?"
        }
        
        response = requests.post(
            f"{BASE_URL}/requests/{request_id}/comments",
            json=payload,
            headers={"Authorization": f"Bearer {token}"}
        )
        
        if response.status_code in [200, 201]:
            log_test("Add Comment", True, "Comment added successfully")
            return True
        else:
            log_test("Add Comment", False, f"Status {response.status_code}")
            return False
    except Exception as e:
        log_test("Add Comment", False, str(e))
        return False


def test_get_comments(token: str, request_id: str) -> bool:
    """Test getting comments for a request"""
    try:
        response = requests.get(
            f"{BASE_URL}/requests/{request_id}/comments",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        if response.status_code == 200:
            comments = response.json()
            log_test("Get Comments", True, f"Found {len(comments)} comments")
            return True
        else:
            log_test("Get Comments", False, f"Status {response.status_code}")
            return False
    except Exception as e:
        log_test("Get Comments", False, str(e))
        return False


def test_submit_request(token: str, request_id: str) -> bool:
    """Test submitting a request for review"""
    try:
        response = requests.post(
            f"{BASE_URL}/workflow/requests/{request_id}/submit",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        if response.status_code == 200:
            data = response.json()
            log_test("Submit Request", True, f"Status: {data['status']}, Next: Stage {data.get('next_stage', {}).get('order_index', 'N/A')}")
            return True
        else:
            log_test("Submit Request", False, f"Status {response.status_code}: {response.text}")
            return False
    except Exception as e:
        log_test("Submit Request", False, str(e))
        return False


def test_get_pending_actions(token: str, user_name: str) -> bool:
    """Test getting pending actions for a user"""
    try:
        response = requests.get(
            f"{BASE_URL}/workflow/pending",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        if response.status_code == 200:
            data = response.json()
            total = data.get("total_pending", 0)
            log_test(f"Get Pending Actions ({user_name})", True, f"Total pending: {total}")
            return True
        else:
            log_test(f"Get Pending Actions ({user_name})", False, f"Status {response.status_code}")
            return False
    except Exception as e:
        log_test(f"Get Pending Actions ({user_name})", False, str(e))
        return False


def test_take_action(token: str, stage_id: str, action: str, user_name: str) -> bool:
    """Test taking action on a workflow stage"""
    try:
        payload = {
            "action": action,
            "comments": f"Test {action.lower()} from {user_name}. Looks good!"
        }
        
        response = requests.post(
            f"{BASE_URL}/workflow/stages/{stage_id}/action",
            json=payload,
            headers={"Authorization": f"Bearer {token}"}
        )
        
        if response.status_code == 200:
            data = response.json()
            log_test(f"Take Action: {action} ({user_name})", True, data.get("message", "Action completed"))
            return True
        else:
            log_test(f"Take Action: {action} ({user_name})", False, f"Status {response.status_code}: {response.text}")
            return False
    except Exception as e:
        log_test(f"Take Action: {action} ({user_name})", False, str(e))
        return False


def test_workflow_history(token: str, request_id: str) -> bool:
    """Test getting workflow history"""
    try:
        response = requests.get(
            f"{BASE_URL}/workflow/requests/{request_id}/history",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        if response.status_code == 200:
            stages = response.json()
            log_test("Get Workflow History", True, f"Total stages: {len(stages)}")
            return True
        else:
            log_test("Get Workflow History", False, f"Status {response.status_code}")
            return False
    except Exception as e:
        log_test("Get Workflow History", False, str(e))
        return False


def print_summary():
    """Print test summary"""
    print("\n" + "="*60)
    print("📊 TEST SUMMARY")
    print("="*60)
    print(f"Total Tests: {tests_passed + tests_failed}")
    print(f"✅ Passed: {tests_passed}")
    print(f"❌ Failed: {tests_failed}")
    
    if tests_failed > 0:
        print("\n❌ Failed Tests:")
        for result in test_results:
            if not result["passed"]:
                print(f"   - {result['test']}: {result['details']}")
    
    print("="*60)
    
    if tests_failed == 0:
        print("🎉 All tests passed!")
    else:
        print(f"⚠️  {tests_failed} test(s) failed")


def main():
    print("="*60)
    print("🧪 PROCESS FLOW API - COMPREHENSIVE TEST SUITE")
    print("="*60)
    print()
    
    # 1. Health checks
    print("🏥 Health Checks")
    print("-" * 60)
    test_health_check()
    test_database_health()
    print()
    
    # 2. User registration/authentication
    print("👥 User Authentication")
    print("-" * 60)
    user1_data = register_user("creator@test.com", "Test123!", "Alice Creator")
    user2_data = register_user("recommender@test.com", "Test123!", "Bob Recommender")
    user3_data = register_user("approver@test.com", "Test123!", "Charlie Approver")
    
    if not all([user1_data, user2_data, user3_data]):
        print("\n❌ Cannot proceed without users. Exiting.")
        print_summary()
        return
    
    # Store tokens and IDs
    test_data["user1_token"] = user1_data["access_token"]
    test_data["user2_token"] = user2_data["access_token"]
    test_data["user3_token"] = user3_data["access_token"]
    test_data["user1_id"] = user1_data["user"]["id"]
    test_data["user2_id"] = user2_data["user"]["id"]
    test_data["user3_id"] = user3_data["user"]["id"]
    print()
    
    # 3. Request management
    print("📝 Request Management")
    print("-" * 60)
    request_id = test_create_request(test_data["user1_token"])
    
    if not request_id:
        print("\n❌ Cannot proceed without request. Exiting.")
        print_summary()
        return
    
    test_data["request_id"] = request_id
    
    test_list_requests(test_data["user1_token"])
    test_get_request_details(test_data["user1_token"], request_id)
    test_update_request(test_data["user1_token"], request_id)
    test_add_comment(test_data["user1_token"], request_id)
    test_get_comments(test_data["user1_token"], request_id)
    print()
    
    # 4. Workflow submission
    print("🚀 Workflow Submission")
    print("-" * 60)
    test_submit_request(test_data["user1_token"], request_id)
    print()
    
    # 5. Pending actions
    print("📋 Pending Actions")
    print("-" * 60)
    test_get_pending_actions(test_data["user1_token"], "Creator")
    test_get_pending_actions(test_data["user2_token"], "Recommender")
    test_get_pending_actions(test_data["user3_token"], "Approver")
    print()
    
    # 6. Workflow actions
    print("✅ Workflow Actions")
    print("-" * 60)
    if test_data.get("stage1_id"):
        test_take_action(test_data["user2_token"], test_data["stage1_id"], "RECOMMENDED", "Bob")
    
    if test_data.get("stage2_id"):
        test_take_action(test_data["user3_token"], test_data["stage2_id"], "APPROVED", "Charlie")
    
    test_workflow_history(test_data["user1_token"], request_id)
    print()
    
    # 7. Final checks
    print("🔍 Final Verification")
    print("-" * 60)
    test_get_request_details(test_data["user1_token"], request_id)
    print()
    
    print_summary()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Tests interrupted by user")
        print_summary()
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {e}")
        print_summary()

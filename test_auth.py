"""
Quick test script to check authentication
"""
import requests
import json

BASE_URL = "http://localhost:5000"

print("Testing Authentication...")
print("=" * 60)

# Test 1: Try to access dashboard without login
print("\n1. Testing dashboard access without login...")
try:
    response = requests.get(f"{BASE_URL}/dashboard/", allow_redirects=False)
    if response.status_code == 302:
        print("   ✓ Dashboard correctly redirects to login (status 302)")
        print(f"   → Redirects to: {response.headers.get('Location', 'unknown')}")
    else:
        print(f"   ✗ Unexpected status: {response.status_code}")
except Exception as e:
    print(f"   ✗ Error: {e}")

# Test 2: Test login endpoint
print("\n2. Testing login endpoint...")
try:
    # You'll need to replace with actual credentials
    login_data = {
        "email": "test@example.com",
        "password": "test123"
    }
    response = requests.post(f"{BASE_URL}/api/login", json=login_data)
    print(f"   Status: {response.status_code}")
    data = response.json()
    if data.get('success'):
        print("   ✓ Login successful")
        print(f"   → Token received: {data.get('token', '')[:20]}...")
        print(f"   → Cookie set: {'token' in response.cookies}")
        token = data.get('token')
        
        # Test 3: Try accessing dashboard with token
        print("\n3. Testing dashboard access with token...")
        cookies = {'token': token}
        response = requests.get(f"{BASE_URL}/dashboard/", cookies=cookies, allow_redirects=False)
        if response.status_code == 200:
            print("   ✓ Dashboard accessible with token")
        elif response.status_code == 302:
            print(f"   ✗ Still redirecting (status 302)")
            print(f"   → Redirects to: {response.headers.get('Location', 'unknown')}")
        else:
            print(f"   ✗ Unexpected status: {response.status_code}")
    else:
        print(f"   ✗ Login failed: {data.get('message', 'Unknown error')}")
        print("   → Create a test user first or use existing credentials")
except Exception as e:
    print(f"   ✗ Error: {e}")

print("\n" + "=" * 60)
print("Test complete!")
print("\nTo test manually:")
print("1. Start server: python auth/integrated_app.py")
print("2. Open browser: http://localhost:5000/login")
print("3. Login with your credentials")
print("4. Check if you can access: http://localhost:5000/dashboard/")


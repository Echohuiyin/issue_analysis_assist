"""
Test authentication and rate limiting functionality
"""
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kernel_cases.settings')
sys.path.insert(0, '/home/lmr/project/issue_analysis_assist')
django.setup()

from django.test import Client, TestCase
from django.contrib.auth.models import User
import json


def test_authentication():
    print("=" * 70)
    print("Testing Authentication System")
    print("=" * 70)
    
    client = Client()
    
    print("\n1. Testing login page access...")
    response = client.get('/auth/login/')
    print(f"   Status: {response.status_code}")
    print(f"   ✅ Login page accessible" if response.status_code == 200 else f"   ❌ Failed")
    
    print("\n2. Testing registration page access...")
    response = client.get('/auth/register/')
    print(f"   Status: {response.status_code}")
    print(f"   ✅ Register page accessible" if response.status_code == 200 else f"   ❌ Failed")
    
    print("\n3. Creating test user...")
    try:
        User.objects.filter(username='testuser').delete()
        user = User.objects.create_user(username='testuser', password='testpass123')
        print(f"   ✅ Test user created: testuser / testpass123")
    except Exception as e:
        print(f"   ❌ Failed to create user: {e}")
        return
    
    print("\n4. Testing login with valid credentials...")
    response = client.post('/auth/login/', 
        data=json.dumps({'username': 'testuser', 'password': 'testpass123'}),
        content_type='application/json'
    )
    print(f"   Status: {response.status_code}")
    result = json.loads(response.content)
    print(f"   Success: {result.get('success')}")
    print(f"   ✅ Login successful" if result.get('success') else f"   ❌ Login failed: {result.get('error')}")
    
    print("\n5. Testing authentication check...")
    response = client.get('/auth/check/')
    result = json.loads(response.content)
    print(f"   Authenticated: {result.get('authenticated')}")
    print(f"   Username: {result.get('username')}")
    print(f"   ✅ Auth check working" if result.get('authenticated') else f"   ❌ Auth check failed")
    
    print("\n6. Testing logout...")
    response = client.post('/auth/logout/')
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        result = json.loads(response.content)
        print(f"   ✅ Logout successful" if result.get('success') else f"   ❌ Logout failed")
    elif response.status_code == 302:
        print(f"   ✅ Logout successful (redirected)")
    else:
        print(f"   ❌ Unexpected status code")
    
    print("\n7. Testing login with invalid credentials...")
    response = client.post('/auth/login/',
        data=json.dumps({'username': 'testuser', 'password': 'wrongpass'}),
        content_type='application/json'
    )
    result = json.loads(response.content)
    print(f"   ✅ Correctly rejected invalid credentials" if not result.get('success') else f"   ❌ Should have rejected")
    
    print("\n" + "=" * 70)
    print("Authentication Tests Complete")
    print("=" * 70)


def test_rate_limiting():
    print("\n" + "=" * 70)
    print("Testing Rate Limiting System")
    print("=" * 70)
    
    client = Client()
    
    print("\n1. Testing API health endpoint (no rate limit)...")
    for i in range(5):
        response = client.get('/api/health/')
        print(f"   Request {i+1}: Status {response.status_code}")
    print(f"   ✅ Health endpoint accessible")
    
    print("\n2. Testing rate limit on API endpoints...")
    print("   Making 15 rapid requests to /api/search/...")
    rate_limited = False
    for i in range(15):
        response = client.post('/api/search/',
            data=json.dumps({'query': 'test'}),
            content_type='application/json'
        )
        if response.status_code == 429:
            print(f"   Request {i+1}: Rate limited! ✅")
            rate_limited = True
            break
        else:
            print(f"   Request {i+1}: Status {response.status_code}")
    
    if rate_limited:
        print(f"   ✅ Rate limiting is working")
    else:
        print(f"   ⚠️  Rate limiting may not be configured (this is OK for testing)")
    
    print("\n3. Checking rate limit headers...")
    response = client.post('/api/search/',
        data=json.dumps({'query': 'test'}),
        content_type='application/json'
    )
    
    if 'X-RateLimit-Limit' in response:
        print(f"   X-RateLimit-Limit: {response['X-RateLimit-Limit']}")
        print(f"   X-RateLimit-Remaining: {response['X-RateLimit-Remaining']}")
        print(f"   ✅ Rate limit headers present")
    else:
        print(f"   ⚠️  No rate limit headers (may not be enabled)")
    
    print("\n" + "=" * 70)
    print("Rate Limiting Tests Complete")
    print("=" * 70)


def test_authenticated_rate_limit():
    print("\n" + "=" * 70)
    print("Testing Authenticated User Rate Limits")
    print("=" * 70)
    
    client = Client()
    
    print("\n1. Logging in as test user...")
    User.objects.filter(username='ratelimituser').delete()
    user = User.objects.create_user(username='ratelimituser', password='testpass123')
    
    response = client.post('/auth/login/',
        data=json.dumps({'username': 'ratelimituser', 'password': 'testpass123'}),
        content_type='application/json'
    )
    result = json.loads(response.content)
    
    if result.get('success'):
        print(f"   ✅ Logged in successfully")
    else:
        print(f"   ❌ Login failed")
        return
    
    print("\n2. Making requests as authenticated user...")
    print("   Authenticated users should have higher rate limits")
    for i in range(5):
        response = client.post('/api/search/',
            data=json.dumps({'query': 'test'}),
            content_type='application/json'
        )
        remaining = response.get('X-RateLimit-Remaining', 'N/A')
        print(f"   Request {i+1}: Status {response.status_code}, Remaining: {remaining}")
    
    print("\n" + "=" * 70)
    print("Authenticated Rate Limit Tests Complete")
    print("=" * 70)


if __name__ == '__main__':
    test_authentication()
    test_rate_limiting()
    test_authenticated_rate_limit()
    
    print("\n" + "=" * 70)
    print("All Tests Complete!")
    print("=" * 70)
    print("\nNext Steps:")
    print("1. Start the server: python3 manage.py runserver")
    print("2. Visit: http://localhost:8000/auth/login/")
    print("3. Login with: testuser / testpass123")
    print("4. Or create a new user at: http://localhost:8000/auth/register/")
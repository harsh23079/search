"""Test script for scraping endpoints."""
import requests
import json
from typing import Dict, Any

BASE_URL = "http://localhost:8000/api/v1"

def test_scrape_instagram():
    """Test Instagram scraping endpoint."""
    print("\n" + "="*60)
    print("Testing Instagram Scraping Endpoint")
    print("="*60)
    
    url = f"{BASE_URL}/scrape"
    
    # Test with Instagram profile URL
    payload = {
        "url": "https://www.instagram.com/nike/",
        "post_limit": 10,
        "use_api": True
    }
    
    print(f"\nRequest URL: {url}")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    
    try:
        response = requests.post(url, json=payload, timeout=300)
        print(f"\nStatus Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"\n✅ Success!")
            print(f"Platform: {data.get('platform')}")
            print(f"Total Posts: {data.get('total_posts')}")
            print(f"Estimated Cost: ${data.get('estimated_cost', 0):.4f}")
            print(f"Message: {data.get('message')}")
            
            if data.get('posts'):
                print(f"\nFirst Post Sample:")
                first_post = data['posts'][0]
                print(f"  Source: {first_post.get('source')}")
                print(f"  Extraction Method: {first_post.get('extraction_method')}")
                if first_post.get('structured_data'):
                    print(f"  Has Structured Data: Yes")
                    print(f"  Keys: {list(first_post['structured_data'].keys())[:5]}...")
        else:
            print(f"\n❌ Error: {response.status_code}")
            print(f"Response: {response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"\n❌ Request failed: {str(e)}")
        print("Make sure the backend is running on http://localhost:8000")

def test_scrape_pinterest():
    """Test Pinterest scraping endpoint."""
    print("\n" + "="*60)
    print("Testing Pinterest Scraping Endpoint")
    print("="*60)
    
    url = f"{BASE_URL}/scrape"
    
    # Test with Pinterest board URL
    payload = {
        "url": "https://www.pinterest.com/pinterest/fashion/",
        "post_limit": 10,
        "use_api": True
    }
    
    print(f"\nRequest URL: {url}")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    
    try:
        response = requests.post(url, json=payload, timeout=300)
        print(f"\nStatus Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"\n✅ Success!")
            print(f"Platform: {data.get('platform')}")
            print(f"Total Posts: {data.get('total_posts')}")
            print(f"Estimated Cost: ${data.get('estimated_cost', 0):.4f}")
            print(f"Message: {data.get('message')}")
            
            if data.get('posts'):
                print(f"\nFirst Post Sample:")
                first_post = data['posts'][0]
                print(f"  Source: {first_post.get('source')}")
                print(f"  Extraction Method: {first_post.get('extraction_method')}")
        else:
            print(f"\n❌ Error: {response.status_code}")
            print(f"Response: {response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"\n❌ Request failed: {str(e)}")
        print("Make sure the backend is running on http://localhost:8000")

def test_batch_scrape():
    """Test batch scraping endpoint."""
    print("\n" + "="*60)
    print("Testing Batch Scraping Endpoint")
    print("="*60)
    
    url = f"{BASE_URL}/scrape/batch"
    
    payload = {
        "urls": [
            "https://www.instagram.com/nike/",
            "https://www.pinterest.com/pinterest/fashion/"
        ],
        "post_limit": 5,
        "use_api": True
    }
    
    print(f"\nRequest URL: {url}")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    
    try:
        response = requests.post(url, json=payload, timeout=600)
        print(f"\nStatus Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"\n✅ Success!")
            print(f"URLs Processed: {data.get('urls_processed')}")
            print(f"URLs Failed: {data.get('urls_failed')}")
            print(f"Total Posts: {data.get('total_posts')}")
            print(f"Total Cost: ${data.get('total_cost', 0):.4f}")
            print(f"Message: {data.get('message')}")
            
            if data.get('errors'):
                print(f"\nErrors: {data.get('errors')}")
        else:
            print(f"\n❌ Error: {response.status_code}")
            print(f"Response: {response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"\n❌ Request failed: {str(e)}")

def test_health():
    """Test if backend is running."""
    print("\n" + "="*60)
    print("Testing Backend Health")
    print("="*60)
    
    try:
        response = requests.get("http://localhost:8000/", timeout=5)
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            print("✅ Backend is running!")
            data = response.json()
            print(f"Message: {data.get('message')}")
            print(f"Version: {data.get('version')}")
            return True
        else:
            print("❌ Backend returned error")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Backend is not running: {str(e)}")
        print("\nPlease start the backend first:")
        print("  docker-compose up -d")
        return False

if __name__ == "__main__":
    print("\n" + "="*60)
    print("SCRAPING ENDPOINTS TEST")
    print("="*60)
    
    # First check if backend is running
    if not test_health():
        print("\n⚠️  Backend is not running. Please start it first.")
        exit(1)
    
    # Test endpoints
    print("\n\nChoose test to run:")
    print("1. Test Instagram scraping")
    print("2. Test Pinterest scraping")
    print("3. Test batch scraping")
    print("4. Run all tests")
    
    choice = input("\nEnter choice (1-4): ").strip()
    
    if choice == "1":
        test_scrape_instagram()
    elif choice == "2":
        test_scrape_pinterest()
    elif choice == "3":
        test_batch_scrape()
    elif choice == "4":
        test_scrape_instagram()
        test_scrape_pinterest()
        test_batch_scrape()
    else:
        print("Invalid choice. Running all tests...")
        test_scrape_instagram()
        test_scrape_pinterest()
        test_batch_scrape()
    
    print("\n" + "="*60)
    print("Testing Complete!")
    print("="*60)


import requests
import os

def test_instagram_downloader():
    """Test the Instagram Downloader application"""
    base_url = "http://localhost:5001"
    
    # Test 1: Health check
    print("Testing health endpoint...")
    try:
        response = requests.get(f"{base_url}/health")
        if response.status_code == 200 and response.json().get('status') == 'healthy':
            print("✓ Health check passed")
        else:
            print("✗ Health check failed")
            return False
    except Exception as e:
        print(f"✗ Health check failed with error: {e}")
        return False
    
    # Test 2: Main page
    print("\nTesting main page...")
    try:
        response = requests.get(f"{base_url}/")
        if response.status_code == 200 and 'InstaSave' in response.text:
            print("✓ Main page loaded successfully")
        else:
            print("✗ Main page failed to load")
            return False
    except Exception as e:
        print(f"✗ Main page test failed with error: {e}")
        return False
    
    # Test 3: Download endpoint with invalid URL
    print("\nTesting download endpoint with invalid URL...")
    try:
        payload = {"url": "https://www.instagram.com/p/invalid"}
        response = requests.post(f"{base_url}/download", json=payload)
        if response.status_code == 400 or ('error' in response.json()):
            print("✓ Download endpoint correctly handled invalid URL")
        else:
            print("✗ Download endpoint didn't handle invalid URL properly")
            return False
    except Exception as e:
        print(f"✗ Download endpoint test failed with error: {e}")
        return False
    
    print("\n✓ All tests passed! The application is working correctly.")
    print("\nTo use the application:")
    print("1. Open your browser and go to http://localhost:5001")
    print("2. Paste an Instagram post URL in the input field")
    print("3. Click 'Download' to retrieve the media")
    return True

if __name__ == "__main__":
    print("Testing Instagram Downloader Application...")
    test_instagram_downloader()
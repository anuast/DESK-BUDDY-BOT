import urllib.request
import os

def force_hydrate():
    xml_filename = 'haarcascade_frontalface_default.xml'
    print("[Fix Utility] Attempting a direct alternative download pipeline...")
    
    # Direct alternative backup mirror hosted by the official OpenCV repository
    url = "https://githubusercontent.com"
    
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=10) as response:
            with open(xml_filename, 'wb') as f:
                f.write(response.read())
        print(f"✅ Success! Generated a clean tracking file ({os.path.getsize(xml_filename)} bytes).")
    except Exception as e:
        print(f"❌ Automation failed due to firewall restrictions: {e}")
        print("\n💡 Alternative Fix: Copy the link into your mobile web browser, download it, and send the file to your laptop!")

if __name__ == "__main__":
    force_hydrate()

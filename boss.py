import pygetwindow as gw
import subprocess
import time
import os

# These are the distractions we are tracking
BANNED_SITES = ["pinterest", "youtube", "instagram", "netflix"]

def start_monitoring():
    print("[Python Boss] Starting background window check... Press Ctrl+C to stop.")
    try:
        while True:
            active_window = gw.getActiveWindow()
            if active_window is not None and active_window.title:
                window_title = active_window.title.lower()
                
                for site in BANNED_SITES:
                    if site in window_title:
                        print(f"\n[Python Boss] Caught you! Window contains: {site}")
                        executable = "./worker.exe" if os.name == 'nt' else "./worker"
                        
                        # This passes your custom WhatsApp audio directly!
                        subprocess.run([executable, "yell_procrastination.mp3"])
                        
                        # Pause for 3 seconds so it doesn't repeatedly loop the audio clip
                        time.sleep(3)
                        break
            time.sleep(2)
    except KeyboardInterrupt:
        print("\n[Python Boss] Monitoring stopped cleanly.")

if __name__ == "__main__":
    start_monitoring()

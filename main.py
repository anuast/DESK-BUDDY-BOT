import threading
import time
import os

# Link your custom standalone modules
from vision_sensor import start_vision_sensor
from boss import start_monitoring

def run_vision_system():
    print("[Master Node] Spawning Computer Vision System Thread... ")
    try:
        start_vision_sensor()
    except Exception as e:
        print(f"[Master Node] Vision System Thread Crashed: {e}")

def run_window_tracker():
    print("[Master Node] Spawning Application Polling Window Thread... ")
    try:
        start_monitoring()
    except Exception as e:
        print(f"[Master Node] Window Tracker Thread Crashed: {e}")

if __name__ == "__main__":
    print("\n=======================================================")
    print(" DESK BUDDY BOT: COMPLETE MULTI-THREADED DEPLOYMENT ")
    print("=======================================================\n")

    # 1. Initialize two asynchronous threads pointing to our tasks
    # daemon=True ensures that when you close main.py, all background tracking stops instantly
    vision_thread = threading.Thread(target=run_vision_system, daemon=True)
    window_thread = threading.Thread(target=run_window_tracker, daemon=True)

    # 2. Begin running both detection models simultaneously
    vision_thread.start()
    window_thread.start()

    # 3. Keep the master thread alive while background workers perform audits
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n[Master Node] All tracking loops successfully disconnected. Stay productive!")

import pygetwindow as gw
import time

from play_audio import play_audio

# These are the distractions we are tracking
BANNED_SITES = ["pinterest", "youtube", "instagram", "netflix"]

def start_monitoring():
    print("[Python Boss] Starting background window check... Press Ctrl+C to stop.")
    try:
        while True:
            active_window = gw.getActiveWindow()
            if active_window is not None:
                # On macOS pygetwindow exposes .title as a callable method,
                # not a plain string property — resolve it either way.
                title = active_window.title
                if callable(title):
                    title = title()
                if not title or not isinstance(title, str):
                    time.sleep(2)
                    continue
                window_title = title.lower()

                for site in BANNED_SITES:
                    if site in window_title:
                        print(f"\n[Python Boss] Caught you! Window contains: {site}")

                        # Play the alert audio via the cross-platform helper
                        play_audio("yell_procrastination.mp3")

                        # Pause so it doesn't repeatedly loop the audio clip
                        time.sleep(3)
                        break
            time.sleep(2)
    except KeyboardInterrupt:
        print("\n[Python Boss] Monitoring stopped cleanly.")

if __name__ == "__main__":
    start_monitoring()

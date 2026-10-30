import os
import sys
import subprocess


def play_audio(filename: str) -> None:
    """Cross-platform audio playback.

    - macOS  : uses the built-in `afplay` command (no extra deps needed).
    - Windows: uses `worker.exe` if present, otherwise falls back to
               PowerShell's MediaPlayer so the bot still works without
               the compiled C++ worker.
    - Linux  : tries `mpg123` (install with: sudo apt install mpg123).
    """
    if not os.path.exists(filename):
        print(f"[Audio] ❌ Missing audio file: '{filename}' — skipping playback.")
        return

    try:
        if sys.platform == "darwin":                      # macOS
            subprocess.run(["afplay", filename], check=True)

        elif os.name == "nt":                             # Windows
            worker = "./worker.exe"
            if os.path.exists(worker):
                subprocess.run([worker, filename], check=True)
            else:
                # Fallback: PowerShell MediaPlayer (no extra install needed)
                abs_path = os.path.abspath(filename).replace("\\", "/")
                ps_cmd = (
                    "Add-Type -AssemblyName presentationCore; "
                    f"$p = New-Object System.Windows.Media.MediaPlayer; "
                    f"$p.Open([uri]'file:///{abs_path}'); "
                    "$p.Play(); Start-Sleep -Seconds 8"
                )
                subprocess.run(["powershell", "-Command", ps_cmd], check=True)

        else:                                             # Linux
            subprocess.run(["mpg123", "-q", filename], check=True)

    except FileNotFoundError as e:
        print(f"[Audio] ❌ Playback command not found: {e}")
    except subprocess.CalledProcessError as e:
        print(f"[Audio] ❌ Playback failed: {e}")

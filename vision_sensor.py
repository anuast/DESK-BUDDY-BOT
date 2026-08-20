import cv2
import time
import subprocess
import os
import threading

class RealTimeCameraStream:
    """An isolated thread class to constantly grab raw camera frames without buffering lag."""
    def __init__(self, src=0):
        # cv2.CAP_DSHOW bypasses Windows OS buffer pipelines for instant frame delivery
        self.stream = cv2.VideoCapture(src + cv2.CAP_DSHOW)
        
        # Optimize hardware processing resolution profiles to save CPU cycles
        self.stream.set(cv2.CAP_PROP_FRAME_WIDTH, 320)
        self.stream.set(cv2.CAP_PROP_FRAME_HEIGHT, 240)
        
        (self.grabbed, self.frame) = self.stream.read()
        self.stopped = False

    def start(self):
        # Spawns a dedicated reading worker separate from main processing execution threads
        threading.Thread(target=self.update, args=(), daemon=True).start()
        return self

    def update(self):
        while not self.stopped:
            if not self.grabbed:
                self.stop()
                break
            (self.grabbed, self.frame) = self.stream.read()

    def read(self):
        return self.frame

    def stop(self):
        self.stopped = True
        self.stream.release()

def start_vision_sensor():
    xml_filename = 'haarcascade_frontalface_default.xml'
    face_cascade = cv2.CascadeClassifier(xml_filename)
    
    if face_cascade.empty():
        print("❌ Critical System Error: Map file empty or missing!")
        return

    # Initialize our non-blocking real-time hardware frame consumer pipeline
    vs = RealTimeCameraStream(src=0).start()
    time.sleep(1.0) # Warm up webcam hardware sensor drivers
    
    print("\n👁️ [Vision Sensor]: High-FPS Threaded Real-Time Stream Deployed Natively...")

    distraction_timer = None
    is_triggered = False

    try:
        while True:
            frame = vs.read()
            if frame is None:
                continue

            frame = cv2.flip(frame, 1)
            h, w, _ = frame.shape
            
            # High-speed grayscale translation matrix transformation
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            
            # Optimized detection coefficients to completely eliminate false processing matches
            faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=6, minSize=(50, 50))

            gaze_status = "Focused"

            if len(faces) > 0:
                # Isolate the largest target mask surface box in the viewfinder grid
                fx, fy, fw, fh = max(faces, key=lambda r: r[2] * r[3])
                face_center_x = fx + (fw // 2)

                # Draw visibility target boundary box over face coordinates
                cv2.rectangle(frame, (fx, fy), (fx + fw, fy + fh), (0, 255, 0), 2)

                # Track position changes relative to the screen center boundaries
                if face_center_x < int(w * 0.32) or face_center_x > int(w * 0.68):
                    gaze_status = "Distracted (Looking Away)"
                    if distraction_timer is None:
                        distraction_timer = time.time()
                    else:
                        if (time.time() - distraction_timer) > 4 and not is_triggered:
                            print("\n🚨 [Vision Sensor]: Look-away threshold breached!")
                            executable = "./worker.exe" if os.name == 'nt' else "./worker"
                            subprocess.run([executable, "yell_procrastination.mp3"])
                            is_triggered = True
                else:
                    distraction_timer = None
                    is_triggered = False
            else:
                gaze_status = "Absent from Desk"
                if distraction_timer is None:
                    distraction_timer = time.time()
                else:
                    if (time.time() - distraction_timer) > 4 and not is_triggered:
                        print("\n🚨 [Vision Sensor]: User missing from workspace space matrix!")
                        executable = "./worker.exe" if os.name == 'nt' else "./worker"
                        subprocess.run([executable, "yell_procrastination.mp3"])
                        is_triggered = True

            # Render data overlay on screen for real-time tracking tracking validation
            color = (0, 255, 0) if gaze_status == "Focused" else (0, 0, 255)
            cv2.putText(frame, f"Gaze Status: {gaze_status}", (15, 30), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
            
            cv2.imshow('Desk Buddy - Universal Vision Sensor Node', frame)

            # Wait 1ms for GUI refresh loop actions to keep system running optimally
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

    except KeyboardInterrupt:
        print("\n👁️ Vision analysis halted safely.")
    finally:
        vs.stop()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    start_vision_sensor()

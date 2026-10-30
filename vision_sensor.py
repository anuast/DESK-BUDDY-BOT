import cv2
import sys
import time
import subprocess
import os
import threading
import urllib.request
from collections import deque

from play_audio import play_audio

# cv2.imshow() requires the main thread on macOS — calling it from a
# background thread raises an "Unknown C++ exception from OpenCV".
# On Windows it works from any thread, so we keep the live preview there.
SHOW_PREVIEW = sys.platform == "win32"

import mediapipe as mp
from mediapipe.tasks.python import BaseOptions
from mediapipe.tasks.python import vision as mp_vision

# ---------------------------------------------------------------------------
# MediaPipe deprecated the old `mp.solutions.face_mesh` API in recent
# releases (0.10.10+) in favor of the Tasks API used below. If you're on an
# older mediapipe (<=0.10.9) the old API still works, but this version
# targets current installs (`pip install mediapipe` today gives you Tasks).
# ---------------------------------------------------------------------------

FACE_LANDMARKER_MODEL_URL = (
    "https://storage.googleapis.com/mediapipe-models/face_landmarker/"
    "face_landmarker/float16/latest/face_landmarker.task"
)
MODEL_PATH = "face_landmarker.task"


def _ensure_model_downloaded():
    """One-time download of the FaceLandmarker model bundle, same pattern
    as fix_xml.py already uses for the haarcascade asset."""
    if os.path.exists(MODEL_PATH) and os.path.getsize(MODEL_PATH) > 0:
        return True
    print(f"[Vision Sensor] Downloading face landmark model to '{MODEL_PATH}' (one-time)...")
    try:
        req = urllib.request.Request(FACE_LANDMARKER_MODEL_URL, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=30) as response:
            with open(MODEL_PATH, 'wb') as f:
                f.write(response.read())
        print(f"✅ Model downloaded ({os.path.getsize(MODEL_PATH)} bytes).")
        return True
    except Exception as e:
        print(f"❌ Could not download the face landmark model: {e}")
        print(f"   Manually download it from:\n   {FACE_LANDMARKER_MODEL_URL}")
        print(f"   and place it next to this script as '{MODEL_PATH}'.")
        return False


# ---------------------------------------------------------------------------
# Camera stream (unchanged — still null-safe against missing cameras)
# ---------------------------------------------------------------------------
class RealTimeCameraStream:
    """An isolated thread class to constantly grab raw camera frames without buffering lag."""
    def __init__(self, src=0):
        self.stream = None
        self.frame = None
        self.grabbed = False

        for index in [0, 1, 2, 3]:
            temp_stream = cv2.VideoCapture(index)
            if temp_stream.isOpened():
                self.stream = temp_stream
                print(f"[Hardware Core] Successfully locked onto active Camera Index: {index}")
                break
            else:
                temp_stream.release()

        if self.stream is None:
            print(" Critical System Error: No operational camera device found on index scan mapping.")
            self.stopped = True
            return

        # Slightly higher res than the original -- landmark accuracy benefits
        # from more pixels; we compensate cost via frame-skipping below.
        self.stream.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.stream.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

        (self.grabbed, self.frame) = self.stream.read()
        self.stopped = False

    def start(self):
        threading.Thread(target=self.update, args=(), daemon=True).start()
        return self

    def update(self):
        while not self.stopped:
            (self.grabbed, self.frame) = self.stream.read()
            if not self.grabbed:
                time.sleep(0.1)
                continue

    def read(self):
        return self.frame

    def stop(self):
        self.stopped = True
        if self.stream is not None and self.stream.isOpened():
            self.stream.release()


# ---------------------------------------------------------------------------
# Face mesh landmark indices we care about. The Tasks API's FaceLandmarker
# outputs the same 478-point topology as the old refine_landmarks=True mesh,
# including irises at indices 468-477.
# ---------------------------------------------------------------------------
LEFT_EYE_CORNERS = (33, 133)     # outer, inner corner of the left eye (viewer's left)
RIGHT_EYE_CORNERS = (362, 263)   # outer, inner corner of the right eye
LEFT_IRIS_CENTER = 468
RIGHT_IRIS_CENTER = 473
NOSE_TIP = 1


def _normalize_brightness(frame):
    """Cheap contrast/brightness normalization so detection holds up in dim or
    backlit rooms, without the cost of full histogram equalization on color frames."""
    return cv2.convertScaleAbs(frame, alpha=1.15, beta=12)


def _eye_gaze_ratio(landmarks, corner_ids, iris_id, w):
    """Returns ~0.5 when the iris is centered between the eye corners,
    <0.5 = looking toward viewer's left, >0.5 = looking toward viewer's right."""
    outer_x = landmarks[corner_ids[0]].x * w
    inner_x = landmarks[corner_ids[1]].x * w
    iris_x = landmarks[iris_id].x * w
    span = inner_x - outer_x
    if abs(span) < 1e-3:
        return 0.5
    return (iris_x - outer_x) / span


def start_vision_sensor():
    if not _ensure_model_downloaded():
        return

    base_options = BaseOptions(model_asset_path=MODEL_PATH)
    options = mp_vision.FaceLandmarkerOptions(
        base_options=base_options,
        running_mode=mp_vision.RunningMode.IMAGE,
        num_faces=1,
        min_face_detection_confidence=0.6,
        min_face_presence_confidence=0.6,
        min_tracking_confidence=0.6,
        output_face_blendshapes=False,
        output_facial_transformation_matrixes=False,
    )
    landmarker = mp_vision.FaceLandmarker.create_from_options(options)

    vs = RealTimeCameraStream(src=0).start()
    if vs.stream is None:
        print("❌ [Vision Sensor]: No camera available — vision sensor thread will not start.")
        landmarker.close()
        return

    time.sleep(1.0)  # warm up webcam

    def detect(frame_bgr):
        """Run FaceLandmarker on a BGR frame, return the first face's landmark list or None."""
        rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
        result = landmarker.detect(mp_image)
        if result.face_landmarks:
            return result.face_landmarks[0]
        return None

    # -----------------------------------------------------------------
    # Calibration: look at the screen normally for ~3 seconds so we can
    # set thresholds relative to YOUR face/webcam geometry, instead of
    # a fixed "32% / 68% of frame width" guess that doesn't fit everyone.
    # -----------------------------------------------------------------
    print("\n🎯 [Vision Sensor]: Calibrating — please look at your screen normally for 3 seconds...")
    calib_nose_x, calib_gaze = [], []
    calib_start = time.time()
    while time.time() - calib_start < 3.0:
        frame = vs.read()
        if frame is None:
            continue
        frame = cv2.flip(frame, 1)
        frame = _normalize_brightness(frame)
        lm = detect(frame)
        if lm is not None:
            h, w, _ = frame.shape
            calib_nose_x.append(lm[NOSE_TIP].x * w)
            l_gaze = _eye_gaze_ratio(lm, LEFT_EYE_CORNERS, LEFT_IRIS_CENTER, w)
            r_gaze = _eye_gaze_ratio(lm, RIGHT_EYE_CORNERS, RIGHT_IRIS_CENTER, w)
            calib_gaze.append((l_gaze + r_gaze) / 2)

    if calib_nose_x:
        baseline_nose_x = sum(calib_nose_x) / len(calib_nose_x)
        baseline_gaze = sum(calib_gaze) / len(calib_gaze)
        print(f"✅ [Vision Sensor]: Calibration complete (baseline nose_x={baseline_nose_x:.1f}, "
              f"baseline_gaze={baseline_gaze:.2f})")
    else:
        baseline_nose_x = None
        baseline_gaze = 0.5
        print("⚠️ [Vision Sensor]: Couldn't see a face during calibration — using default thresholds.")

    if SHOW_PREVIEW:
        print("\n👁️ [Vision Sensor]: High-FPS Threaded Real-Time Stream Deployed Natively... (press Q in preview window to quit)")
    else:
        print("\n👁️ [Vision Sensor]: High-FPS Threaded Real-Time Stream Deployed Natively... (headless mode on macOS)")

    distraction_timer = None
    is_triggered = False

    # Rolling window smoothing: only act on a status once it's been the
    # majority verdict over the last ~15 processed frames, killing
    # single-frame flicker false positives.
    status_history = deque(maxlen=15)

    # Frame skipping: run the (relatively expensive) landmark inference
    # every N frames and hold the last known status in between, freeing
    # up budget for the higher capture resolution above.
    PROCESS_EVERY_N_FRAMES = 3
    frame_count = 0
    last_gaze_status = "Focused"

    try:
        while True:
            raw_frame = vs.read()
            if raw_frame is None:
                continue

            frame = cv2.flip(raw_frame, 1)
            h, w, _ = frame.shape
            frame_count += 1

            if frame_count % PROCESS_EVERY_N_FRAMES == 0:
                proc_frame = _normalize_brightness(frame)
                lm = detect(proc_frame)

                if lm is not None:
                    xs = [p.x * w for p in lm]
                    ys = [p.y * h for p in lm]
                    fx, fy, fx2, fy2 = int(min(xs)), int(min(ys)), int(max(xs)), int(max(ys))

                    # Draw bounding box — Windows only (imshow not safe from thread on macOS)
                    if SHOW_PREVIEW:
                        cv2.rectangle(frame, (fx, fy), (fx2, fy2), (0, 255, 0), 2)

                    nose_x = lm[NOSE_TIP].x * w
                    l_gaze = _eye_gaze_ratio(lm, LEFT_EYE_CORNERS, LEFT_IRIS_CENTER, w)
                    r_gaze = _eye_gaze_ratio(lm, RIGHT_EYE_CORNERS, RIGHT_IRIS_CENTER, w)
                    gaze_ratio = (l_gaze + r_gaze) / 2

                    # Head-yaw check (relative to calibrated baseline, else frame center)
                    head_ref = baseline_nose_x if baseline_nose_x is not None else w / 2
                    head_offset = abs(nose_x - head_ref) / w  # normalized 0..1

                    # Eye-direction check (relative to calibrated baseline gaze ratio)
                    eye_offset = abs(gaze_ratio - baseline_gaze)

                    # Distracted if EITHER the head has turned meaningfully away
                    # OR the eyes have drifted off-center within the sockets,
                    # even with the head still pointed forward (e.g. looking at phone).
                    if head_offset > 0.12 or eye_offset > 0.18:
                        last_gaze_status = "Distracted (Looking Away)"
                    else:
                        last_gaze_status = "Focused"
                else:
                    last_gaze_status = "Absent from Desk"

                status_history.append(last_gaze_status)

            gaze_status = last_gaze_status

            # Require the smoothed majority vote before acting on distraction/absence,
            # so a single bad frame doesn't fire the alert.
            if len(status_history) == status_history.maxlen:
                distracted_votes = sum(1 for s in status_history if s == "Distracted (Looking Away)")
                absent_votes = sum(1 for s in status_history if s == "Absent from Desk")
                total = len(status_history)

                if distracted_votes / total > 0.7:
                    if distraction_timer is None:
                        distraction_timer = time.time()
                    elif (time.time() - distraction_timer) > 4 and not is_triggered:
                        print("\n🚨 [Vision Sensor]: Look-away threshold breached!")
                        play_audio("yell_procrastination.mp3")
                        is_triggered = True
                elif absent_votes / total > 0.7:
                    if distraction_timer is None:
                        distraction_timer = time.time()
                    elif (time.time() - distraction_timer) > 4 and not is_triggered:
                        print("\n🚨 [Vision Sensor]: User missing from workspace space matrix!")
                        play_audio("yell_procrastination.mp3")
                        is_triggered = True
                else:
                    distraction_timer = None
                    is_triggered = False

            # Live preview window — Windows only (macOS requires GUI on main thread)
            if SHOW_PREVIEW:
                color = (0, 255, 0) if gaze_status == "Focused" else (0, 0, 255)
                cv2.putText(frame, f"Gaze Status: {gaze_status}", (15, 30),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
                cv2.imshow('Desk Buddy - Universal Vision Sensor Node', frame)
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break

    except KeyboardInterrupt:
        print("\n👁️ Vision analysis halted safely.")
    finally:
        vs.stop()
        landmarker.close()
        if SHOW_PREVIEW:
            cv2.destroyAllWindows()


if __name__ == "__main__":
    start_vision_sensor()

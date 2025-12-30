"""
Screen Recorder - records the entire bot session continuously
"""
import time
import threading
import os
from datetime import datetime
from mss import mss
import numpy as np
import cv2
from modules.helper import log_print


class ScreenRecorder:
    """
    Records screen continuously during bot operation.
    Starts when initialized, stops when stop_recording() is called.
    """
    
    def __init__(self, output_dir="recordings", fps=5, quality="medium"):
        """
        Initialize screen recorder.
        
        Args:
            output_dir: Directory to save recordings (default: "recordings")
            fps: Frames per second (default: 5 for smaller files)
            quality: Video quality - "low", "medium", "high" (default: "medium")
        """
        self.output_dir = output_dir
        self.fps = fps
        self.quality = quality
        self.recording = False
        self.frames = []
        self.thread = None
        self.lock = threading.Lock()
        # Don't create mss() here - create it in the recording thread
        
        # Quality settings for video encoding
        quality_settings = {
            "low": {"fourcc": cv2.VideoWriter_fourcc(*'mp4v'), "bitrate": 1000},
            "medium": {"fourcc": cv2.VideoWriter_fourcc(*'mp4v'), "bitrate": 2000},
            "high": {"fourcc": cv2.VideoWriter_fourcc(*'XVID'), "bitrate": 4000}
        }
        self.video_settings = quality_settings.get(quality, quality_settings["medium"])
        
        # Create output directory if it doesn't exist
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Generate filename with timestamp
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        self.filename = os.path.join(self.output_dir, f"Bot_Session_{timestamp}.mp4")
        
        log_print(f"Screen recorder initialized - will save to: {self.filename}")
    
    def start_recording(self):
        """Start recording screen in background thread."""
        if self.recording:
            log_print("Recording already in progress")
            return False
        
        self.recording = True
        self.frames = []
        
        # Start recording thread
        self.thread = threading.Thread(target=self._record_loop, daemon=True)
        self.thread.start()
        
        log_print(f"Screen recording started (FPS: {self.fps}, Quality: {self.quality})")
        return True
    
    def stop_recording(self):
        """Stop recording and save video file."""
        if not self.recording:
            log_print("No recording in progress")
            return None
        
        log_print("Stopping screen recording and saving video...")
        
        # Stop recording loop
        self.recording = False
        
        # Wait for thread to finish (with timeout)
        if self.thread:
            self.thread.join(timeout=10)
        
        # Save video
        if self.frames:
            try:
                self._save_video()
                log_print(f"Screen recording saved: {self.filename}")
                return self.filename
            except Exception as e:
                log_print(f"Error saving video: {str(e)}")
                import traceback
                log_print(f"Traceback: {traceback.format_exc()}")
                return None
        else:
            log_print("No frames captured - nothing to save")
            return None
    
    def _record_loop(self):
        """Main recording loop - captures screen frames."""
        # Create mss instance in this thread (required for thread-local storage)
        sct = mss()
        
        frame_interval = 1.0 / self.fps
        last_capture_time = time.time()
        
        # Get screen dimensions (primary monitor)
        monitor = sct.monitors[1]  # monitors[0] is all monitors, [1] is primary
        width = monitor["width"]
        height = monitor["height"]
        
        log_print(f"Recording screen: {width}x{height} at {self.fps} FPS")
        
        while self.recording:
            try:
                current_time = time.time()
                
                # Capture frame if enough time has passed
                if current_time - last_capture_time >= frame_interval:
                    # Capture screen
                    screenshot = sct.grab(monitor)
                    
                    # Convert to numpy array and then to BGR for OpenCV
                    img = np.array(screenshot)
                    img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
                    
                    # Store frame
                    with self.lock:
                        self.frames.append(img.copy())
                    
                    last_capture_time = current_time
                else:
                    # Sleep a bit to avoid busy waiting
                    time.sleep(0.01)
                    
            except Exception as e:
                # Log error but continue recording
                log_print(f"Error capturing frame: {str(e)}")
                time.sleep(0.1)
        
        log_print(f"Recording stopped - captured {len(self.frames)} frames")
    
    def _save_video(self):
        """Save captured frames to video file."""
        if not self.frames:
            log_print("No frames to save")
            return
        
        # Get frame dimensions from first frame
        height, width = self.frames[0].shape[:2]
        
        # Create video writer
        fourcc = self.video_settings["fourcc"]
        out = cv2.VideoWriter(
            self.filename,
            fourcc,
            self.fps,
            (width, height)
        )
        
        if not out.isOpened():
            raise Exception(f"Failed to open video writer for {self.filename}")
        
        # Write all frames
        log_print(f"Saving {len(self.frames)} frames to video...")
        for i, frame in enumerate(self.frames):
            out.write(frame)
            if (i + 1) % 100 == 0:
                log_print(f"Saved {i + 1}/{len(self.frames)} frames...")
        
        # Release video writer
        out.release()
        
        # Get file size
        file_size_mb = os.path.getsize(self.filename) / (1024 * 1024)
        log_print(f"Video saved: {self.filename} ({file_size_mb:.2f} MB)")
    
    def is_recording(self):
        """Check if currently recording."""
        return self.recording
    
    def get_filename(self):
        """Get the output filename."""
        return self.filename
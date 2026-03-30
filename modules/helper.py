"""
Helper functions for bot operations: logging, recording, reporting, screen management
"""
import os
import csv
import time
import queue
import ctypes
from ctypes import wintypes
from datetime import datetime
import threading
import requests
from pywinauto import Desktop, mouse
from pywinauto.keyboard import send_keys
from config import API_BASE_URL, API_AUTH_HEADER, MACHINE_NAME, BOT_NAME, SCRC_SECRET_KEY, API_LOG_ENABLED, API_LOG_BATCH_SIZE, API_LOG_ENDPOINT, API_TIMEOUT, API_LOG_BATCH_INTERVAL, UI_ACTION_TIMEOUT
import pyotp

# === Constants ===
REPORTS_FOLDER = "reports"
MAX_FAILURES = 3

# Global log file
log_file = None

# Global screen recorder
screen_recorder = None

# Global heartbeat manager
heartbeat_manager = None
# Global log queue manager
log_queue_manager = None

# === Logging Functions ===
class LogQueueManager:
    """
    Manages async API logging using a queue and background thread.
    Sends logs to API in batches without blocking the main code.
    """
    
    def __init__(self):
        self.queue = queue.Queue()
        self.worker_thread = None
        self.running = False
        # Create logs directory if it doesn't exist
        logs_dir = "logs"
        if not os.path.exists(logs_dir):
            os.makedirs(logs_dir)
        self.last_sent_line_file = os.path.join(logs_dir, "last_sent_line.txt")
        self.batch = []
        self.last_batch_time = time.time()
        
    def start(self):
        """Start the background worker thread"""
        if not API_LOG_ENABLED:
            return
        
        self.running = True
        self.worker_thread = threading.Thread(target=self._worker, daemon=True)
        self.worker_thread.start()
        
        # Send any missed logs from file on startup
        self._send_missed_logs()
    
    def stop(self):
        """Stop the background worker thread and send remaining logs"""
        if not self.running:
            return
        
        self.running = False
        
        # Drain queue and add to batch
        try:
            while not self.queue.empty():
                try:
                    log_entry = self.queue.get_nowait()
                    self.batch.append(log_entry)
                except queue.Empty:
                    break
        except:
            pass
        
        # Send any remaining logs in batch
        if self.batch:
            self._send_batch_to_api()
            self.batch = []
        
        # Give worker thread a moment to finish
        try:
            if self.worker_thread:
                self.worker_thread.join(timeout=2)
        except:
            pass
    
    def add_log(self, timestamp, message):
        """Add a log message to the queue (non-blocking)"""
        if not API_LOG_ENABLED:
            return
        
        try:
            self.queue.put_nowait({
                'timestamp': timestamp,
                'message': message
            })
        except queue.Full:
            # Queue is full, skip this log (don't block)
            pass
    
    def _worker(self):
        """Background worker thread that processes the queue"""
        while self.running:
            try:
                # Collect logs from queue (try to get multiple before checking)
                collected_any = False
                for _ in range(API_LOG_BATCH_SIZE):
                    try:
                        log_entry = self.queue.get(timeout=0.1)
                        self.batch.append(log_entry)
                        collected_any = True
                    except queue.Empty:
                        break
                
                # Check if we should send batch
                should_send = False
                current_time = time.time()
                
                # Send if batch size reached
                if len(self.batch) >= API_LOG_BATCH_SIZE:
                    should_send = True
                
                # Send if time interval reached and we have logs
                elif self.batch and (current_time - self.last_batch_time) >= API_LOG_BATCH_INTERVAL:
                    should_send = True
                
                if should_send:
                    self._send_batch_to_api()
                    self.batch = []
                    self.last_batch_time = current_time
                elif not collected_any:
                    # No logs collected, sleep a bit
                    time.sleep(0.1)
                
            except Exception as e:
                # Don't let errors in worker thread crash the app
                error_msg = f"Error in log queue worker: {str(e)}"
                print(error_msg)
                self._write_error_to_log_file(error_msg)
                time.sleep(1)
    
    def _send_batch_to_api(self):
        """Send a batch of logs to the API"""
        if not self.batch:
            return
        
        try:
            payload = {
                "bot_name": BOT_NAME,
                "server_name": MACHINE_NAME,
                "logs": [
                    {
                        "timestamp": log['timestamp'],
                        "message": log['message']
                    }
                    for log in self.batch
                ]
            }
            
            response = requests.post(
                API_LOG_ENDPOINT,
                json=payload,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": API_AUTH_HEADER
                },
                timeout=API_TIMEOUT
            )
            
            if response.status_code != 200:
                error_msg = f"API log send failed with status {response.status_code}, response: {response.text}"
                self._write_error_to_log_file(error_msg)
                
        except requests.exceptions.RequestException as e:
            # Don't block if API fails - log error to file
            error_msg = f"Failed to send logs to API: {str(e)}"
            print(error_msg)
            self._write_error_to_log_file(error_msg)
        except Exception as e:
            error_msg = f"Error sending logs to API: {str(e)}"
            print(error_msg)
            self._write_error_to_log_file(error_msg)
    
    def _write_error_to_log_file(self, error_message):
        """Write error message directly to log file (bypasses queue to avoid circular dependency)"""
        try:
            global log_file
            if log_file:
                timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                log_file.write(f"{timestamp} - [LOG QUEUE ERROR] {error_message}\n")
                log_file.flush()
        except:
            pass
    
    def _send_missed_logs(self):
        """Read log file and send any missed logs on startup"""
        if not os.path.exists(self.last_sent_line_file):
            # First time running, don't send old logs
            return
        
        try:
            # Read last sent line number
            with open(self.last_sent_line_file, 'r') as f:
                last_sent_line = int(f.read().strip())
        except:
            # If file is corrupted, start from beginning
            last_sent_line = 0
        
        # Get current log file path (in logs directory)
        logs_dir = "logs"
        date_str = datetime.now().strftime('%Y-%m-%d')
        log_file_path = os.path.join(logs_dir, f"log_{date_str}.txt")
        
        if not os.path.exists(log_file_path):
            return
        
        try:
            # Read log file from last sent line
            with open(log_file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                
            # Get new lines
            new_lines = lines[last_sent_line:]
            
            if not new_lines:
                return
            
            # Parse and send new logs
            batch = []
            for line in new_lines:
                # Parse log line: "2025-11-26 15:04:40 - message"
                parts = line.split(' - ', 1)
                if len(parts) == 2:
                    timestamp = parts[0].strip()
                    message = parts[1].strip()
                    batch.append({
                        'timestamp': timestamp,
                        'message': message
                    })
            
            if batch:
                # Send in batches
                for i in range(0, len(batch), API_LOG_BATCH_SIZE):
                    chunk = batch[i:i + API_LOG_BATCH_SIZE]
                    self.batch = chunk
                    self._send_batch_to_api()
                    self.batch = []
                    time.sleep(0.1)  # Small delay between batches
                
                # Update last sent line
                with open(self.last_sent_line_file, 'w') as f:
                    f.write(str(len(lines)))
                    
        except Exception as e:
            error_msg = f"Error sending missed logs: {str(e)}"
            print(error_msg)
            self._write_error_to_log_file(error_msg)
    
    def update_last_sent_line(self, line_number):
        """Update the last sent line number"""
        try:
            with open(self.last_sent_line_file, 'w') as f:
                f.write(str(line_number))
        except:
            pass

def init_log_file(file_path=None):
    """Initialize log file with date-based naming in logs directory."""
    global log_file
    
    logs_dir = "logs"
    os.makedirs(logs_dir, exist_ok=True)
    
    if file_path is None:
        date_str = datetime.now().strftime('%Y-%m-%d')
        file_path = os.path.join(logs_dir, f"log_{date_str}.txt")
    elif not os.path.dirname(file_path):
        file_path = os.path.join(logs_dir, file_path)
    
    log_file = open(file_path, "a", encoding="utf-8")


def close_log_file():
    """Close the log file."""
    global log_file
    if log_file:
        log_file.close()
        log_file = None


def log_print(message):
    """Print to console and write to log file."""
    print(message)
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    if log_file:
        log_file.write(f"{timestamp} - {message}\n")
        log_file.flush()
    
    # Add to API queue (non-blocking)
    if log_queue_manager:
        log_queue_manager.add_log(timestamp, message)

def init_heartbeat():
    """
    Initialize and start the heartbeat manager.
    Reads configuration directly from config.py.
    
    Returns:
        HeartbeatManager instance (already started)
    """
    global heartbeat_manager
    
    # Lazy import to avoid circular dependency
    from modules.heartbeat import HeartbeatManager
    
    heartbeat_api_url = API_BASE_URL + "rpa_get_bot_status.php"
    heartbeat_manager = HeartbeatManager(
        api_url=heartbeat_api_url,
        auth_header=API_AUTH_HEADER,
        server_name=MACHINE_NAME,
        bot_name=BOT_NAME,
        interval=30,
        timeout=3
    )
    heartbeat_manager.start()
    return heartbeat_manager

def otp_generator():
    totp = pyotp.TOTP(SCRC_SECRET_KEY)
    # Current 6-digit TOTP code
    code = totp.now()
    return code

def check_and_wait_if_paused():
    """
    Check if bot is paused by server and wait until it's active again.
    Uses the global heartbeat_manager to check status.
    
    Returns:
        True when bot is active and can continue
    """
    global heartbeat_manager
    
    if heartbeat_manager is None:
        # No heartbeat manager, assume active
        return True
    
    # Check if bot should be paused
    while not heartbeat_manager.is_bot_active():
        log_print("Bot is paused by server. Waiting for activation...")
        time.sleep(10)  # Check every 10 seconds
    
    return True


def stop_heartbeat():
    """Stop the heartbeat manager."""
    global heartbeat_manager
    
    if heartbeat_manager:
        heartbeat_manager.stop()
        heartbeat_manager = None


def run_with_timeout(func, timeout_seconds=60):
    """Run func in a daemon thread; raise TimeoutError if it doesn't finish in time."""
    result, error = [None], [None]
    def _target():
        try:
            result[0] = func()
        except Exception as e:
            error[0] = e
    t = threading.Thread(target=_target, daemon=True)
    t.start()
    t.join(timeout=timeout_seconds)
    if t.is_alive():
        raise TimeoutError(f"Operation timed out after {timeout_seconds}s")
    if error[0]:
        raise error[0]
    return result[0]


# === .NET Error Dialog Handler ===

def check_and_close_dotnet_error_dialog():
    """
    Check for and close the .NET error dialog by clicking Continue.
    
    Continue button coordinates: (1016, 582)
    Fallback: Alt+C keyboard shortcut
    
    Returns:
        True if dialog was found and closed, False if no dialog found
    """
    log_print("Checking for .NET error dialog...")
    
    desktop = Desktop(backend="uia")
    
    # Look for "eIVF .Net" window
    for win in desktop.windows():
        try:
            win_title = win.window_text()
            
            if win_title == "eIVF .Net":
                log_print("*** FOUND 'eIVF .Net' dialog ***")
                
                # Method 1: Click at Continue button coordinates
                try:
                    log_print("Clicking Continue button at (1016, 582)...")
                    run_with_timeout(lambda: mouse.click(coords=(1016, 582)), timeout_seconds=UI_ACTION_TIMEOUT)
                    log_print("*** Clicked Continue button! ***")
                    time.sleep(1)
                    return True
                except Exception as click_err:
                    log_print(f"Coordinate click failed: {click_err}")
                
                # Method 2: Alt+C keyboard shortcut as fallback
                try:
                    log_print("Trying Alt+C keyboard shortcut...")
                    run_with_timeout(lambda: (win.set_focus(), time.sleep(0.3), send_keys("%c")), timeout_seconds=UI_ACTION_TIMEOUT)
                    log_print("*** Sent Alt+C ***")
                    time.sleep(1)
                    return True
                except Exception as key_err:
                    log_print(f"Alt+C failed: {key_err}")
                    
        except Exception:
            continue
    
    log_print("No .NET error dialog found")
    return False


# === Screen Recording Functions ===
def start_recording(output_dir=None, fps=5, quality="medium", max_file_size_gb=2):
    """
    Start screen recording for the entire bot session.
    Auto-rotates to new file when size reaches max_file_size_gb.
    
    Args:
        output_dir: Directory to save recordings (default: from config.RECORDINGS_DIR)
        fps: Frames per second (default: 5 for smaller files)
        quality: Video quality - "low", "medium", "high" (default: "medium")
        max_file_size_gb: Max file size in GB before creating new file (default: 5)
    
    Returns:
        True if recording started successfully, False otherwise
    """
    global screen_recorder
    
    from config import RECORDINGS_DIR
    if output_dir is None:
        output_dir = RECORDINGS_DIR
    
    try:
        # Import here to avoid circular dependencies
        import modules.screen_recorder as screen_recorder_module
        
        screen_recorder = screen_recorder_module.ScreenRecorder(
            output_dir=output_dir,
            fps=fps,
            quality=quality,
            max_file_size_gb=max_file_size_gb
        )
        screen_recorder.start_recording()
        log_print(f"Screen recording started for entire session (auto-rotate at {max_file_size_gb}GB)")
        return True
    except Exception as e:
        log_print(f"WARNING: Failed to start screen recording: {str(e)}")
        log_print("Continuing without screen recording...")
        screen_recorder = None
        return False


def stop_recording():
    """
    Stop screen recording and save the video file.
    Simple interface - all complexity is handled internally.
    
    Returns:
        str: Path to saved recording file, or None if no recording was active
    """
    global screen_recorder
    
    if not screen_recorder:
        return None
    
    try:
        recording_file = screen_recorder.stop_recording()
        if recording_file:
            log_print(f"Screen recording saved: {recording_file}")
        return recording_file
    except Exception as e:
        log_print(f"Error stopping screen recording: {str(e)}")
        return None
    finally:
        screen_recorder = None


def cleanup_old_recordings(recordings_dir=None, days_old=2):
    """Delete files older than specified days from recordings folder."""
    import time
    from config import RECORDINGS_DIR
    
    if recordings_dir is None:
        recordings_dir = RECORDINGS_DIR
    
    try:
        if not os.path.exists(recordings_dir):
            return
        cutoff_time = time.time() - (days_old * 24 * 60 * 60)
        for filename in os.listdir(recordings_dir):
            filepath = os.path.join(recordings_dir, filename)
            if os.path.isfile(filepath) and os.path.getmtime(filepath) < cutoff_time:
                os.remove(filepath)
                log_print(f"Deleted old file: {filename}")
    except Exception as e:
        log_print(f"Cleanup error: {e}")


def take_screenshot(prefix="screenshot"):
    """
    Take a screenshot and save it to the recordings folder.
    
    Args:
        prefix: Prefix for the screenshot filename (default: "screenshot")
    
    Returns:
        str: Path to saved screenshot file, or None if failed
    """
    try:
        from PIL import ImageGrab
        from config import RECORDINGS_DIR
        
        # Create recordings directory if it doesn't exist
        output_dir = RECORDINGS_DIR
        os.makedirs(output_dir, exist_ok=True)
        
        # Generate filename with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{prefix}_{timestamp}.png"
        filepath = os.path.join(output_dir, filename)
        
        # Capture screenshot
        screenshot = ImageGrab.grab()
        screenshot.save(filepath)
        
        log_print(f"Screenshot saved: {filepath}")
        return filepath
        
    except Exception as e:
        log_print(f"Error taking screenshot: {str(e)}")
        return None


# === Patient Report Functions ===

def get_daily_report_file():
    """Get path to today's report file."""
    os.makedirs(REPORTS_FOLDER, exist_ok=True)
    today = datetime.now().strftime('%Y-%m-%d')
    return os.path.join(REPORTS_FOLDER, f"patient_report_{today}.csv")


def load_patient_report():
    """Load existing patient report from today's CSV."""
    report = {}
    content_keys = set()
    report_file = get_daily_report_file()
    if os.path.exists(report_file):
        with open(report_file, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                key = f"{row['patient_phone']}_{row['patient_first_name']}_{row['clinic_name']}_{row['note_id']}"
                report[key] = row
                if row.get('status') == 'success' and row.get('note'):
                    ckey = f"{row.get('patient_first_name','')}_{row.get('patient_last_name','')}_{row.get('patient_dob','')}_{row.get('patient_phone','')}_{row.get('note','')}"
                    content_keys.add(ckey)
    return report, content_keys


def save_patient_to_report(note_data, status, failure_count=0):
    """Save patient result to today's report CSV."""
    report_file = get_daily_report_file()
    file_exists = os.path.exists(report_file)
    
    with open(report_file, 'a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(['note_id', 'patient_first_name', 'patient_last_name', 
                           'patient_phone', 'patient_dob', 'clinic_name', 'status', 'failure_count', 
                           'last_attempt_time', 'note'])
        writer.writerow([
            note_data['note_id'],
            note_data['patient_first_name'],
            note_data['patient_last_name'],
            note_data['patient_phone'],
            note_data.get('patient_dob', ''),
            note_data['clinic_name'],
            status,
            failure_count,
            datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            note_data.get('note', '')
        ])


def filter_notes_by_report(notes, patient_report, content_keys=None, update_api_fn=None):
    """Filter out already processed or max-failed notes.
    Also skips duplicate content (same patient+note) already succeeded, calling update_api if provided."""
    skipped = []
    indices_to_keep = []
    if content_keys is None:
        content_keys = set()
    
    for idx, note in notes.iterrows():
        key = f"{note['patient_phone']}_{note['patient_first_name']}_{note['clinic_name']}_{note['note_id']}"
        
        if key in patient_report:
            record = patient_report[key]
            if record['status'] == 'success':
                skipped.append((note, "Already processed successfully"))
                continue
            if int(record.get('failure_count', 0)) >= MAX_FAILURES:
                skipped.append((note, f"Max failures ({MAX_FAILURES}) reached"))
                continue
        
        # Check if same content was already processed successfully with a different note_id
        ckey = f"{note['patient_first_name']}_{note['patient_last_name']}_{note.get('patient_dob','')}_{note['patient_phone']}_{note.get('note','')}"
        if ckey in content_keys:
            log_print(f"Duplicate content found for {note['patient_first_name']} {note['patient_last_name']} (note_id: {note['note_id']}) - skipping & updating API")
            if update_api_fn:
                update_api_fn(note['note_id'])
            save_patient_to_report(dict(note), 'success', 0)
            skipped.append((note, "Duplicate content - already processed"))
            continue
        
        indices_to_keep.append(idx)
    
    filtered_notes = notes.loc[indices_to_keep].reset_index(drop=True)
    return filtered_notes, skipped


# === Screen Resolution Functions ===

def get_screen_resolution():
    """Get current screen resolution using Windows API."""
    try:
        user32 = ctypes.windll.user32
        width = user32.GetSystemMetrics(0)  # SM_CXSCREEN
        height = user32.GetSystemMetrics(1)  # SM_CYSCREEN
        return (width, height)
    except:
        return (None, None)


def get_and_log_screen_resolution(context=""):
    """Get screen resolution and log it."""
    try:
        desktop = Desktop(backend="uia")
        desktop_rect = desktop.window().rectangle()
        width = desktop_rect.width()
        height = desktop_rect.height()
        
        context_str = f" [{context}]" if context else ""
        log_print(f"Screen Resolution{context_str}: {width} X {height}")
        return (width, height)
    except:
        width, height = get_screen_resolution()
        if width and height:
            context_str = f" [{context}]" if context else ""
            log_print(f"Screen Resolution{context_str}: {width} X {height}")
            return (width, height)
        return (None, None)


def set_screen_resolution(width=1920, height=1080):
    """Set screen resolution using Windows API."""
    try:
        current_width, current_height = get_screen_resolution()
        if current_width == width and current_height == height:
            log_print(f"Screen resolution already set to {width} X {height}")
            return True
        
        log_print(f"Current resolution: {current_width} X {current_height}")
        log_print(f"Setting resolution to {width} X {height}...")
        
        # Define DEVMODE structure
        class DEVMODE(ctypes.Structure):
            _fields_ = [
                ("dmDeviceName", ctypes.c_wchar * 32),
                ("dmSpecVersion", ctypes.c_ushort),
                ("dmDriverVersion", ctypes.c_ushort),
                ("dmSize", ctypes.c_ushort),
                ("dmDriverExtra", ctypes.c_ushort),
                ("dmFields", ctypes.c_ulong),
                ("dmOrientation", ctypes.c_short),
                ("dmPaperSize", ctypes.c_short),
                ("dmPaperLength", ctypes.c_short),
                ("dmPaperWidth", ctypes.c_short),
                ("dmScale", ctypes.c_short),
                ("dmCopies", ctypes.c_short),
                ("dmDefaultSource", ctypes.c_short),
                ("dmPrintQuality", ctypes.c_short),
                ("dmColor", ctypes.c_short),
                ("dmDuplex", ctypes.c_short),
                ("dmYResolution", ctypes.c_short),
                ("dmTTOption", ctypes.c_short),
                ("dmCollate", ctypes.c_short),
                ("dmFormName", ctypes.c_wchar * 32),
                ("dmLogPixels", ctypes.c_ushort),
                ("dmBitsPerPel", ctypes.c_ulong),
                ("dmPelsWidth", ctypes.c_ulong),
                ("dmPelsHeight", ctypes.c_ulong),
                ("dmDisplayFlags", ctypes.c_ulong),
                ("dmDisplayFrequency", ctypes.c_ulong),
            ]
        
        user32 = ctypes.windll.user32
        dm = DEVMODE()
        dm.dmSize = ctypes.sizeof(DEVMODE)
        dm.dmPelsWidth = width
        dm.dmPelsHeight = height
        dm.dmFields = 0x00080000 | 0x00100000  # DM_PELSWIDTH | DM_PELSHEIGHT
        
        # Test then apply
        if user32.ChangeDisplaySettingsW(ctypes.byref(dm), 0x00000002) != 0:
            log_print(f"Resolution {width} X {height} not supported")
            return False
        
        if user32.ChangeDisplaySettingsW(ctypes.byref(dm), 0x00000001) == 0:
            time.sleep(0.5)
            new_w, new_h = get_screen_resolution()
            if new_w == width and new_h == height:
                log_print(f"Resolution set to {width} X {height}")
                return True
        
        log_print("Failed to set resolution")
        return False
        
    except Exception as e:
        log_print(f"Error setting resolution: {str(e)}")
        return False


def init_log_queue_manager():
    """
    Initialize and start the log queue manager for async API logging.
    
    Returns:
        LogQueueManager instance (already started)
    """
    global log_queue_manager
    if not API_LOG_ENABLED:
        return None
    
    log_queue_manager = LogQueueManager()
    log_queue_manager.start()
    return log_queue_manager

def close_log_queue_manager():
    """Stop the log queue manager and send remaining logs"""
    global log_queue_manager
    if log_queue_manager:
        log_queue_manager.stop()
        log_queue_manager = None

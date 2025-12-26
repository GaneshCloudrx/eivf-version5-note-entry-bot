"""
Helper functions for bot operations: logging, recording, reporting, screen management
"""
import os
import csv
import time
import ctypes
from ctypes import wintypes
from datetime import datetime

from pywinauto import Desktop, mouse
from pywinauto.keyboard import send_keys
from config import API_BASE_URL, API_AUTH_HEADER, MACHINE_NAME, BOT_NAME

# === Constants ===
REPORTS_FOLDER = "reports"
MAX_FAILURES = 2

# Global log file
log_file = None

# Global screen recorder
screen_recorder = None

# Global heartbeat manager
heartbeat_manager = None


# === Logging Functions ===

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
                    mouse.click(coords=(1016, 582))
                    log_print("*** Clicked Continue button! ***")
                    time.sleep(1)
                    return True
                except Exception as click_err:
                    log_print(f"Coordinate click failed: {click_err}")
                
                # Method 2: Alt+C keyboard shortcut as fallback
                try:
                    log_print("Trying Alt+C keyboard shortcut...")
                    win.set_focus()
                    time.sleep(0.3)
                    send_keys("%c")  # Alt+C
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

def start_recording(output_dir="recordings", fps=5, quality="medium"):
    """Start screen recording for the bot session."""
    global screen_recorder
    
    try:
        import modules.screen_recorder as screen_recorder_module
        
        screen_recorder = screen_recorder_module.ScreenRecorder(
            output_dir=output_dir,
            fps=fps,
            quality=quality
        )
        screen_recorder.start_recording()
        log_print("Screen recording started")
        return True
    except Exception as e:
        log_print(f"WARNING: Failed to start screen recording: {str(e)}")
        screen_recorder = None
        return False


def stop_recording():
    """Stop screen recording and save the video file."""
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


# === Patient Report Functions ===

def get_daily_report_file():
    """Get path to today's report file."""
    os.makedirs(REPORTS_FOLDER, exist_ok=True)
    today = datetime.now().strftime('%Y-%m-%d')
    return os.path.join(REPORTS_FOLDER, f"patient_report_{today}.csv")


def load_patient_report():
    """Load existing patient report from today's CSV."""
    report = {}
    report_file = get_daily_report_file()
    if os.path.exists(report_file):
        with open(report_file, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                key = f"{row['patient_phone']}_{row['patient_first_name']}_{row['clinic_name']}"
                report[key] = row
    return report


def save_patient_to_report(note_data, status, failure_count=0):
    """Save patient result to today's report CSV."""
    report_file = get_daily_report_file()
    file_exists = os.path.exists(report_file)
    
    with open(report_file, 'a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(['note_id', 'patient_first_name', 'patient_last_name', 
                           'patient_phone', 'clinic_name', 'status', 'failure_count', 
                           'last_attempt_time'])
        writer.writerow([
            note_data['note_id'],
            note_data['patient_first_name'],
            note_data['patient_last_name'],
            note_data['patient_phone'],
            note_data['clinic_name'],
            status,
            failure_count,
            datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        ])


def filter_notes_by_report(notes, patient_report):
    """Filter out already processed or max-failed patients."""
    skipped = []
    indices_to_keep = []
    
    for idx, note in notes.iterrows():
        key = f"{note['patient_phone']}_{note['patient_first_name']}_{note['clinic_name']}"
        
        if key in patient_report:
            record = patient_report[key]
            if record['status'] == 'success':
                skipped.append((note, "Already processed successfully"))
                continue
            if int(record.get('failure_count', 0)) >= MAX_FAILURES:
                skipped.append((note, f"Max failures ({MAX_FAILURES}) reached"))
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

"""
Utility functions for logging and debugging
"""
from datetime import datetime
import time
import re
from pywinauto import Application, Desktop

# Global log file
log_file = None

def init_log_file(file_path=None):
    """
    Initialize the log file with date-based naming.
    If file_path is provided, uses that; otherwise generates date-based filename.
    Opens in append mode so multiple runs in same day append to same file.
    """
    global log_file
    if file_path is None:
        # Generate date-based filename: log_YYYY-MM-DD.txt
        date_str = datetime.now().strftime('%Y-%m-%d')
        file_path = f"log_{date_str}.txt"
    # Open in append mode - creates if doesn't exist, appends if exists
    log_file = open(file_path, "a", encoding="utf-8")

def close_log_file():
    """Close the log file"""
    global log_file
    if log_file:
        log_file.close()
        log_file = None

def log_print(message):
    """Print to console and write to log file"""
    print(message)
    if log_file:
        log_file.write(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - {message}\n")
        log_file.flush()  # Ensure it's written immediately

def log_rx_status(rx_number, status, error_message=None):
    """
    Log Rx processing status to the main log file with a parseable format.
    Format: [RX_STATUS] Rx Number: <rx_number> - <status> [error_message]
    This can be easily parsed from the log file for business reporting.
    
    Args:
        rx_number: The Rx number (string or int)
        status: "SUCCESS" or "ERROR"
        error_message: Optional error message if status is ERROR
    """
    if status == "SUCCESS":
        log_print(f"[RX_STATUS] Rx Number: {rx_number} - SUCCESS")
    else:
        error_msg = error_message or "Unknown error"
        log_print(f"[RX_STATUS] Rx Number: {rx_number} - ERROR: {error_msg}")

def wait_and_connect_to_window(window_text=None, title_check_func=None, title_re=None, max_wait_time=10):
    """
    Dynamically wait for a window to appear and connect to it.
    
    Args:
        window_text: Exact window title string (e.g., "Rx Profile")
        title_check_func: Function that takes window title and returns True if match (e.g., lambda t: t.startswith("Fill Rx"))
        title_re: Regex pattern for window title (e.g., "^(Fill|Edit) Rx.*")
        max_wait_time: Maximum seconds to wait (default 10)
    
    Returns:
        (app, window) tuple or (None, None) if not found
    
    Note: Provide exactly one of window_text, title_check_func, or title_re
    """
    wait_attempts = max_wait_time * 2  # 0.5 second intervals
    
    for _ in range(wait_attempts):
        time.sleep(0.5)
        try:
            desktop = Desktop(backend="uia")
            for win in desktop.windows():
                try:
                    win_text = win.window_text()
                    if not win_text:
                        continue
                    
                    # Check if window matches criteria
                    matches = False
                    if window_text:
                        matches = (win_text == window_text)
                    elif title_check_func:
                        matches = title_check_func(win_text)
                    elif title_re:
                        matches = bool(re.match(title_re, win_text))
                    
                    if matches:
                        # Found the window, connect to it using process ID
                        process_id = win.element_info.process_id
                        app = Application(backend="uia").connect(process=process_id)
                        
                        # Get window using the same criteria
                        if window_text:
                            window = app[window_text]
                        elif title_re:
                            window = app.window(title_re=title_re)
                        else:
                            # For title_check_func, find by exact title
                            window = app[win_text]
                        
                        return app, window
                except:
                    pass
        except:
            pass
    
    return None, None

def print_all_elements(element, indent=0, max_depth=3):
    """Recursively print all UI elements with their properties"""
    if indent > max_depth:
        return
    try:
        prefix = "  " * indent
        element_type = element.element_info.control_type
        name = element.element_info.name
        auto_id = element.element_info.automation_id
        log_print(f"{prefix}[{element_type}] Name: '{name}' AutoID: '{auto_id}'")
        
        # Try to get children
        try:
            children = element.children()
            for child in children:
                print_all_elements(child, indent + 1, max_depth)
        except:
            pass
    except:
        pass


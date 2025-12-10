"""
Patient search module - handles patient search
"""
from pywinauto import Application, Desktop
import time
from modules.utils import log_print


def get_eivf_main_window():
    """
    Find and connect to the main eIVF window (ThunderRT6MDIForm).
    Returns: (app, main_window) tuple or (None, None) if not found
    """
    desktop = Desktop(backend="uia")
    
    for win in desktop.windows():
        try:
            win_title = win.window_text()
            win_class = win.element_info.class_name
            if win_title.lower() == "eivf" and win_class == "ThunderRT6MDIForm":
                process_id = win.element_info.process_id
                log_print(f"Found main eIVF window (Title: '{win_title}', Class: {win_class}, PID: {process_id})")
                
                # Connect to the application properly
                app = Application(backend="uia").connect(process=process_id)
                main_window = app.window(title=win_title, class_name="ThunderRT6MDIForm")
                return app, main_window
        except:
            pass
    
    return None, None


def open_patient_search(window):
    """
    Open patient search window by clicking the patient search pane/button
    """
    log_print("\n=== Opening Patient Search ===")
    try:
        # Get the main eIVF window
        app, main_window = get_eivf_main_window()
        
        if not main_window:
            log_print("Could not find main eIVF window")
            return False
        
        # Navigate to the left sidebar pane (Pane11 -> Pane12 -> Pane13 with auto_id="100")
        # The patient search is in the left sidebar area
        left_sidebar = main_window.child_window(auto_id="100", control_type="Pane", found_index=0)
        left_sidebar.click_input()
        log_print("Patient search pane clicked")
        time.sleep(1)  # Wait for window to open
        
    except Exception as e:
        log_print(f"Error opening patient search: {str(e)}")
        return False
    return True

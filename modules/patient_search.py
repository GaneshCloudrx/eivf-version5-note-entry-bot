"""
Patient search module - handles patient search
"""
from pywinauto import Application, Desktop
import time
from modules.utils import log_print
from modules.popups import detect_popup, handle_popup

def patient_search(window):
    """
    Perform patient search
    """
    log_print("\n=== Performing Patient Search ===")
    try:
        # Find and fill patient search field using automation ID
        log_print("Entering patient search...")
        try:
            patient_search_field = window.child_window(auto_id="10", class_name="ThunderRT6TextBox")
            patient_search_field.set_focus()
            time.sleep(0.3)
            patient_search_field.type_keys("^a{DELETE}", with_spaces=True)
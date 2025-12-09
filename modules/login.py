"""
Login module - handles application opening and user login
"""
from pywinauto import Application, Desktop
import time
from modules.utils import log_print
from modules.popups import detect_popup, handle_popup

def open_application(app_path, target_title, max_wait_time=30):
    """
    Open the eIVF application if not already open. Ensures only one instance is running.
    Returns: (app, window) tuple or (None, None) if failed
    """
    log_print("=== Opening Application ===")
    desktop = Desktop(backend="uia")
    target_class = "ThunderRT6FormDC"  # VB6 application class

    # Check if already open - look for VB6 window class
    for win in desktop.windows():
        try:
            win_title = win.window_text()
            win_class = win.element_info.class_name

            # Must match both title AND class (to avoid Windows Explorer folders)
            if win_title == target_title and win_class == target_class:
                process_id = win.element_info.process_id
                log_print(f"Found existing eIVF application (PID: {process_id}, Class: {win_class})")
                try:
                    # Connect to this existing instance
                    existing_app = Application(backend="uia").connect(process=process_id)
                    existing_window = existing_app.window(title=target_title, class_name=target_class)
                    existing_window.wait('visible', timeout=5)
                    log_print("Application is already open - using existing instance")
                    return existing_app, existing_window
                except Exception as e:
                    log_print(f"Could not connect to existing window: {str(e)}")
                    pass
            elif win_title == target_title:
                log_print(f"Skipping window '{win_title}' with class '{win_class}' (not VB6 app)")
        except Exception as e:
            pass

    # Application not found, start a new instance
    log_print(f"Starting application: {app_path}")
    try:
        app = Application(backend="uia").start(app_path)
        log_print("Application started! Waiting for window...")

        # Wait for window to appear
        for i in range(max_wait_time):  # Wait up to max_wait_time seconds
            time.sleep(1)
            log_print(f"Waiting... {i+1}s")

            # Check for VB6 window
            for win in desktop.windows():
                try:
                    win_title = win.window_text()
                    win_class = win.element_info.class_name

                    if win_title == target_title and win_class == target_class:
                        log_print(f"Found window: '{win_title}' (Class: {win_class})")
                        process_id = win.element_info.process_id
                        app = Application(backend="uia").connect(process=process_id)
                        window = app.window(title=target_title, class_name=target_class)
                        window.wait('visible', timeout=5)
                        log_print("Application window appeared and connected")
                        return app, window
                except:
                    pass

        log_print(f"ERROR: Could not find eIVF application window after {max_wait_time} seconds")
    except Exception as e:
        log_print(f"Error starting application: {str(e)}")
        import traceback
        log_print(f"Traceback: {traceback.format_exc()}")

    log_print("Failed to open application")
    return None, None

def close_application(window):
    """
    Close the application by clicking the Cancel button on the login window.
    Returns: True if successful, False otherwise
    """
    log_print("Closing application")
    try:
        cancel_button = window.child_window(auto_id="uxCancel", control_type="Button")
        if cancel_button.exists():
            cancel_button.click_input()
            time.sleep(1)
            log_print("Application closed")
            return True
        else:
            log_print("Cancel button not found")
            return False
    except Exception as e:
        log_print(f"Error closing application: {str(e)}")
        return False

def login(window, email, pin, clinic_code):
    """
    Perform login with email and password.
    Returns: True if successful, False otherwise
    """
    log_print("\n=== Logging In ===")
    try:
        # Find and fill email field using automation ID
        # VB6 app uses numeric AutomationIds - "7" is the username field
        log_print("Entering email...")
        try:
            username_field = window.child_window(auto_id="7", class_name="ThunderRT6TextBox")
            username_field.set_focus()
            time.sleep(0.3)
            # Clear any existing text using double-click and Backspace (Ctrl+A doesn't work in this window)
            username_field.double_click_input()
            time.sleep(0.2)
            username_field.type_keys("{BACKSPACE}", with_spaces=True)
            time.sleep(0.2)
            # Type username character by character for reliability
            username_field.type_keys(email, with_spaces=True)
            time.sleep(0.5)
        except Exception as e:
            log_print(f"Error entering email: {str(e)}")
            return False

        # Find and fill password field
        log_print("Entering password...")
        try:
            password_field = window.child_window(auto_id="8", class_name="ThunderRT6TextBox")
            password_field.set_focus()
            time.sleep(0.3)
            # Clear any existing text using double-click and Backspace (Ctrl+A doesn't work in this window)
            password_field.double_click_input()
            time.sleep(0.2)
            password_field.type_keys("{BACKSPACE}", with_spaces=True)
            time.sleep(0.2)
            password_field.type_keys(pin, with_spaces=True)
            time.sleep(0.5)
        except Exception as e:
            log_print(f"Error entering password: {str(e)}")
            return False
        
        # log_print("Entering Clinic Code...")
        # try:
        #     # Clinic code is a ComboBox, not a TextBox
        #     clinic_code_field = window.child_window(auto_id="10", class_name="ThunderRT6ComboBox")
        #     clinic_code_field.set_focus()
        #     time.sleep(0.3)
        #     clinic_code_field.type_keys(clinic_code, with_spaces=True)
        #     time.sleep(0.5)
        # except Exception as e:
        #     log_print(f"Error entering clinic code: {str(e)}")
        #     return False

        # Click login button
        log_print("Clicking login button...")
        try:
            # OK button has AutomationId "5" and class "ThunderRT6CommandButton"
            login_button = window.child_window(auto_id="5", class_name="ThunderRT6CommandButton")
            login_button.click_input()
            time.sleep(2)  # Wait for login to process
            log_print("Login button clicked successfully")
        except Exception as e:
            log_print(f"Error clicking login button: {str(e)}")
            import traceback
            log_print(f"Traceback: {traceback.format_exc()}")
            # Try alternative click method
            try:
                log_print("Trying alternative click method...")
                login_button = window.child_window(auto_id="5", class_name="ThunderRT6CommandButton")
                login_button.invoke()
                time.sleep(2)
                log_print("Login button clicked using invoke()")
            except Exception as e2:
                log_print(f"Alternative click method also failed: {str(e2)}")
                return False

        log_print("Email and password entered, logon button clicked")

        # Wait for either popup (login error) or Rx Profile window (success)
        # Check both simultaneously to minimize wait time
        desktop = Desktop(backend="uia")
        max_wait = 15  # Maximum 15 seconds
        wait_attempts = max_wait * 2  # Check every 0.5 seconds

        for attempt in range(wait_attempts):
            time.sleep(0.5)

            # First, check for Rx Profile window (success case - fastest path)
            try:
                for win in desktop.windows():
                    try:
                        if win.window_text() == "Rx Profile":
                            log_print("Login successful - Rx Profile window detected")
                            return True
                    except:
                        pass
            except:
                pass

            # Only check for popup after first 2 seconds (popups take time to appear)
            if attempt >= 4:  # After 2 seconds (4 * 0.5)
                popup_info = detect_popup(
                    window=window,
                    title_contains='Logon Failed',
                    max_wait_time=1  # Quick check, don't wait long
                )

                if popup_info:
                    popup_title = popup_info.get('title', 'Login Failed')
                    log_print(f"Found popup: {popup_title}")
                    handled = handle_popup(popup_info)
                    if handled:
                        # If popup was handled, login failed
                        return False
                    else:
                        return False

        # If we get here, Rx Profile not found and no popup
        log_print("Rx Profile window not detected - login may still be processing")
        return True  # Return True anyway to let the next step handle it
    except Exception as e:
        log_print(f"Login failed: {str(e)}")
        return False
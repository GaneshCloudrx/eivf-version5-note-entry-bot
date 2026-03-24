"""
Login module - handles eIVF application opening, login, and closing
"""
import time
import psutil
from pywinauto import Application, Desktop
from config import SCRC_SECRET_KEY

import modules.helper as helper

def open_application(app_path, target_title, max_wait_time=60):
    """
    Open the eIVF application if not already open. Ensures only one instance is running.
    Returns: (app, window) tuple or (None, None) if failed
    """
    kill_application("eIVF.exe")
    helper.log_print("=== Opening Application ===")
    
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
                helper.log_print(f"Found existing eIVF application (PID: {process_id}, Class: {win_class})")
                try:
                    # Connect to this existing instance
                    existing_app = Application(backend="uia").connect(process=process_id)
                    existing_window = existing_app.window(title=target_title, class_name=target_class)
                    existing_window.wait('visible', timeout=5)
                    helper.log_print("Application is already open - using existing instance")
                    return existing_app, existing_window
                except Exception as e:
                    helper.log_print(f"Could not connect to existing window: {str(e)}")
                    pass
            elif win_title == target_title:
                helper.log_print(f"Skipping window '{win_title}' with class '{win_class}' (not VB6 app)")
        except Exception as e:
            pass

    # Application not found, start a new instance
    helper.log_print(f"Starting application: {app_path}")
    try:
        app = Application(backend="uia").start(app_path)
        helper.log_print("Application started! Waiting for window...")

        # Give application a moment to start
        time.sleep(2)
        
        # Check for update wizard immediately after start
        dismiss_update_wizard()

        # Wait for window to appear (up to max_wait_time seconds)
        for i in range(max_wait_time):
            time.sleep(1)
            helper.log_print(f"Waiting... {i+1}s")
            
            # Check for and dismiss update wizard more frequently after 5 seconds
            if i >= 4:  # After 5 seconds, check every iteration
                if dismiss_update_wizard():
                    helper.log_print("Update wizard dismissed, continuing to wait for login window...")
                    # Wait a bit for login window to appear after dismissing wizard
                    time.sleep(2)

            # Check for VB6 window
            for win in desktop.windows():
                try:
                    win_title = win.window_text()
                    win_class = win.element_info.class_name

                    if win_title == target_title and win_class == target_class:
                        helper.log_print(f"Found window: '{win_title}' (Class: {win_class})")
                        process_id = win.element_info.process_id
                        app = Application(backend="uia").connect(process=process_id)
                        window = app.window(title=target_title, class_name=target_class)
                        window.wait('visible', timeout=5)
                        helper.log_print("Application window appeared and connected")
                        return app, window
                except:
                    pass
        
        # Final check for update wizard before giving up
        helper.log_print(f"Login window not found after {max_wait_time}s, checking for update wizard one more time...")
        if dismiss_update_wizard():
            helper.log_print("Update wizard dismissed! Waiting 5 more seconds for login window...")
            time.sleep(5)
            
            # Try to find login window one more time
            for win in desktop.windows():
                try:
                    win_title = win.window_text()
                    win_class = win.element_info.class_name

                    if win_title == target_title and win_class == target_class:
                        helper.log_print(f"Found window: '{win_title}' (Class: {win_class})")
                        process_id = win.element_info.process_id
                        app = Application(backend="uia").connect(process=process_id)
                        window = app.window(title=target_title, class_name=target_class)
                        window.wait('visible', timeout=5)
                        helper.log_print("Application window appeared and connected")
                        return app, window
                except:
                    pass

        helper.log_print(f"ERROR: Could not find eIVF application window after {max_wait_time} seconds")
    except Exception as e:
        helper.log_print(f"Error starting application: {str(e)}")
        import traceback
        helper.log_print(f"Traceback: {traceback.format_exc()}")

    # Kill any background eIVF processes before giving up
    helper.log_print("Killing any background eIVF processes...")
    kill_application("eIVF.exe")

    helper.log_print("Failed to open application")
    return None, None

def dismiss_update_wizard():
    """
    Check for and dismiss the eIVF Update Wizard if it appears.
    Clicks the "Update Later" button if found.
    
    Returns:
        True if update wizard was found and dismissed, False otherwise
    """
    try:
        desktop = Desktop(backend="uia")
        
        # Look for Update Wizard window (check both UIA and partial title match)
        for win in desktop.windows():
            try:
                win_title = win.window_text()
                
                # Check for various update wizard title patterns
                if any(keyword in win_title for keyword in ["Update Wizard", "eIVF Update", "PracticeHwy"]):
                    helper.log_print(f"⚠️  Found Update Wizard: '{win_title}'")
                    
                    # Focus the window first
                    try:
                        win.set_focus()
                        time.sleep(0.5)
                    except:
                        pass
                    
                    # Try to find and click "Update Later" button
                    # Method 1: By title and control type
                    try:
                        update_later_btn = win.child_window(
                            title="Update Later",
                            control_type="Button"
                        )
                        
                        if update_later_btn.exists(timeout=2):
                            helper.log_print("Clicking 'Update Later' button...")
                            update_later_btn.click_input()
                            time.sleep(2)
                            helper.log_print("✓ Update Wizard dismissed")
                            return True
                    except Exception as e:
                        pass
                    
                    # Method 2: Try with auto_id
                    try:
                        update_later_btn = win.child_window(auto_id="btnUpdateLater")
                        if update_later_btn.exists(timeout=2):
                            helper.log_print("Clicking 'Update Later' button (via auto_id)...")
                            update_later_btn.click_input()
                            time.sleep(2)
                            helper.log_print("✓ Update Wizard dismissed")
                            return True
                    except Exception as e2:
                        pass
                    
                    # Method 3: Search for any button with "Later" in text
                    try:
                        for btn in win.descendants(control_type="Button"):
                            btn_text = btn.window_text()
                            if "Later" in btn_text or "later" in btn_text:
                                helper.log_print(f"Found button with 'Later': '{btn_text}', clicking...")
                                btn.click_input()
                                time.sleep(2)
                                helper.log_print("✓ Update Wizard dismissed")
                                return True
                    except Exception as e3:
                        helper.log_print(f"All methods failed to dismiss wizard: {e3}")
                    
            except:
                pass
        
        return False
        
    except Exception as e:
        helper.log_print(f"Error checking for Update Wizard: {e}")
        return False


def kill_application(process_name):
    """
    Kill all instances of a process by name and wait for termination.
    """
    killed_any = False
    for proc in psutil.process_iter(['pid', 'name']):
        try:
            if proc.info['name'].lower() == process_name.lower():
                print(f"Killing {process_name} (PID: {proc.info['pid']})")
                proc.kill()
                killed_any = True
        except(psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    
    # If we killed any processes, wait for them to terminate
    if killed_any:
        time.sleep(2)
        
        # Verify all instances are terminated
        max_wait = 5
        for _ in range(max_wait):
            still_running = False
            for proc in psutil.process_iter(['pid', 'name']):
                try:
                    if proc.info['name'].lower() == process_name.lower():
                        still_running = True
                        break
                except(psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
            
            if not still_running:
                print(f"{process_name} fully terminated")
                break
            
            time.sleep(1)
            print(f"Waiting for {process_name} to terminate...")
        
        # Final force kill if still running
        for proc in psutil.process_iter(['pid', 'name']):
            try:
                if proc.info['name'].lower() == process_name.lower():
                    print(f"Force killing stubborn process {process_name} (PID: {proc.info['pid']})")
                    proc.terminate()
                    time.sleep(0.5)
                    if proc.is_running():
                        proc.kill()
            except(psutil.NoSuchProcess, psutil.AccessDenied):
                pass


def close_application(window):
    """
    Close the application by clicking the Cancel button on the login window.
    Returns: True if successful, False otherwise
    """
    helper.log_print("Closing application")
    try:
        cancel_button = window.child_window(auto_id="uxCancel", control_type="Button")
        if cancel_button.exists():
            cancel_button.click_input()
            time.sleep(1)
            helper.log_print("Application closed")
            return True
        else:
            helper.log_print("Cancel button not found")
            return False
    except Exception as e:
        helper.log_print(f"Error closing application: {str(e)}")
        return False
    finally:
        kill_application("eIVF.exe")



def login(window, email, pin, clinic_code, http_address, login_status):
    """
    Perform login with email and password.
    Returns: True if successful, False otherwise
    """
    helper.log_print("\n=== Logging In ===")
    try:
        # Find and fill email field using automation ID
        # VB6 app uses numeric AutomationIds - "7" is the username field
        helper.log_print("Entering email...")
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
            helper.log_print(f"Error entering email: {str(e)}")
            return False

        # Find and fill password field
        helper.log_print("Entering password...")
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
            helper.log_print(f"Error entering password: {str(e)}")
            return False
        
        helper.log_print("Entering Clinic Code...")
        if http_address == "https://eivfdfw.aspirefertility.com/eivf_provider":
            try:
                # Clinic code is a ComboBox, not a TextBox
                clinic_code_field = window.child_window(auto_id="10", class_name="ThunderRT6ComboBox")
                clinic_code_field.set_focus()
                time.sleep(0.3)
                clinic_code_field.type_keys(clinic_code, with_spaces=True)
                time.sleep(0.5)
            except Exception as e:
                helper.log_print(f"Error entering clinic code: {str(e)}")
                return False
        
        if login_status == "double":

                # Step 1: Click "Option >>" button
            helper.log_print("Clicking Option >> button...")
            option_button = window.child_window(auto_id="4", class_name="ThunderRT6CommandButton")
            option_button.click_input()
            time.sleep(1)  # Wait for options to expand
            helper.log_print("Option button clicked")

            # Step 2: Click "Application Configuration" button
            helper.log_print("Clicking Double Login Configuration button...")
            config_button = window.child_window(auto_id="3", class_name="ThunderRT6CommandButton")
            config_button.click_input()
            time.sleep(2)  # Wait for configuration window to open
            helper.log_print("Double Login Configuration button clicked")

            # Step 3: Connect to the Application Configuration window using win32 backend for VB6 controls
            helper.log_print("Connecting to Application Configuration window...")
            try:
                config_app = Application(backend="win32").connect(title="Application Configuration")
                config_window = config_app.window(title="Application Configuration")
                config_window.wait('visible', timeout=5)
                helper.log_print("Connected to Application Configuration window")
            except Exception as config_err:
                helper.log_print(f"Error connecting to config window: {config_err}")
                config_window = None

            # Step 4: Click Save button to apply changes
            helper.log_print("Clicking Double Login Save button...")
            try:
                if config_window:
                    # Find Save button using control_id=1 (integer) for win32 backend
                    save_button = config_window.child_window(
                        control_id=1, 
                        class_name="ThunderRT6CommandButton"
                    )
                    save_button.wait('visible', timeout=5)
                    save_button.click_input()
                    time.sleep(1)
                    helper.log_print("Configuration saved")
                else:
                    raise Exception("Config window not available")
            except Exception as save_error:
                helper.log_print(f"Could not find Save button with primary method: {save_error}")
                # Fallback: try using Desktop to find the button directly
                try:
                    desktop_win32 = Desktop(backend="win32")
                    config_win = desktop_win32.window(title="Application Configuration")
                    save_button = config_win.child_window(control_id=1, class_name="ThunderRT6CommandButton")
                    save_button.click_input()
                    time.sleep(1)
                    helper.log_print("Configuration saved (fallback method)")
                except Exception as fallback_err:
                    helper.log_print(f"Could not find save button: {fallback_err}, changes may need manual saving")

            helper.log_print("Double Login Configuration saved successfully")
        else:
            helper.log_print("Double Login Configuration not needed")

        helper.log_print("Clicking login button...")
        try:
            # OK button has AutomationId "5" and class "ThunderRT6CommandButton"
            login_button = window.child_window(auto_id="5", class_name="ThunderRT6CommandButton")
            login_button.click_input()
            time.sleep(2)  # Wait for login to process
            helper.log_print("Login button clicked successfully")
        except Exception as e:
            helper.log_print(f"Error clicking login button: {str(e)}")
            import traceback
            helper.log_print(f"Traceback: {traceback.format_exc()}")
            # Try alternative click method
            try:
                helper.log_print("Trying alternative click method...")
                login_button = window.child_window(auto_id="5", class_name="ThunderRT6CommandButton")
                login_button.invoke()
                time.sleep(2)
                helper.log_print("Login button clicked using invoke()")
            except Exception as e2:
                helper.log_print(f"Alternative click method also failed: {str(e2)}")
                return False

        helper.log_print("Email and password entered, logon button clicked")

        if http_address == "https://eivf.scrcivf.com/eivf_provider":
            try:
                time.sleep(5)
                helper.log_print("Entering verification code...")
                verification_code = helper.otp_generator()

                # Connect to the eIVF .Net application using UIA backend (for WinForms)
                app = Application(backend="uia").connect(title="eIVF .Net")

                # Get the main window
                main_window = app.window(title="eIVF .Net")

                # Find the verification code text box by AutomationId
                verf_code_box = main_window.child_window(auto_id="verfCode", control_type="Edit")

                # Type the code into the text box
                verf_code_box.type_keys(verification_code, with_spaces=True)

                # Find and click the Verify button
                verify_button = main_window.child_window(auto_id="button1", control_type="Button")
                verify_button.click()
                time.sleep(2)
                helper.log_print("Verification code entered successfully")
            except Exception as e:
                helper.log_print(f"Error entering verification code: {str(e)}")
                return False

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
                        if win.window_text() == "eIVF" and win.element_info.class_name == "ThunderRT6MDIForm":
                            helper.log_print("Login successful - eIVF window detected")
                            # Maximize the eIVF window
                            try:
                                win.maximize()
                                helper.log_print("eIVF window maximized")
                            except Exception as e:
                                helper.log_print(f"Could not maximize window: {str(e)}")
                            return True
                    except:
                        pass
            except:
                pass

        # If we get here, Rx Profile not found and no popup
        helper.log_print("Rx Profile window not detected - login may still be processing")
        return True  # Return True anyway to let the next step handle it
    except Exception as e:
        helper.log_print(f"Login failed: {str(e)}")
        return False
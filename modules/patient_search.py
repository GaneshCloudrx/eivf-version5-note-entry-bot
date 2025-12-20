from pywinauto import Application, Desktop, mouse
from pywinauto.keyboard import send_keys
import time
import re
from modules.utils import log_print


# Cached Patient Search window for reuse across functions
_cached_patient_search_window = None


def wrap_window_properly(window):
    """
    Ensure window has child_window() method by wrapping it properly.
    UIAWrapper objects from descendants() don't have child_window().
    This function connects to the window via its handle to get full functionality.
    """
    if window is None:
        return None
    
    # Check if window already has child_window method
    if hasattr(window, 'child_window'):
        return window
    
    # Try to get handle and connect properly
    try:
        handle = window.handle
        if handle:
            # Connect to the window using its handle
            app = Application(backend="uia").connect(handle=handle)
            wrapped_window = app.window(handle=handle)
            log_print(f"Window wrapped properly via handle: {handle}")
            return wrapped_window
    except Exception as e:
        log_print(f"Could not wrap window via handle: {str(e)[:50]}")
    
    # Fallback: try to connect via process ID
    try:
        pid = window.element_info.process_id
        if pid:
            app = Application(backend="uia").connect(process=pid)
            # Try to find the Patient Search window
            try:
                wrapped = app.window(title_re=".*Patient.*Search.*")
                if wrapped.exists(timeout=1):
                    log_print(f"Window wrapped properly via PID: {pid}")
                    return wrapped
            except:
                pass
    except Exception as e:
        log_print(f"Could not wrap window via PID: {str(e)[:50]}")
    
    # Return original if wrapping fails
    return window


def get_cached_patient_search_window():
    """Get the cached Patient Search window."""
    global _cached_patient_search_window
    return _cached_patient_search_window


def set_cached_patient_search_window(window):
    """Set the cached Patient Search window (properly wrapped)."""
    global _cached_patient_search_window
    # Wrap the window to ensure it has child_window() method
    _cached_patient_search_window = wrap_window_properly(window)
    if _cached_patient_search_window:
        log_print("Patient Search window cached for reuse")


def clear_cached_patient_search_window():
    """Clear the cached Patient Search window."""
    global _cached_patient_search_window
    _cached_patient_search_window = None
    log_print("Patient Search window cache cleared")


# Reusable Desktop instance for UIA backend
def get_desktop():
    """Get Desktop instance with UIA backend."""
    return Desktop(backend="uia")


def get_eivf_main_window():
    """
    Find and connect to the main eIVF window (ThunderRT6MDIForm).
    Returns: (app, main_window) tuple or (None, None) if not found
    """
    desktop = get_desktop()

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


def click_sidebar_icon(main_window, icon_index):
    """
    Click on a specific icon in the pvOutlookGroup sidebar pane.

    The sidebar contains icons that are not exposed as separate UI elements.
    Icons are arranged vertically with approximately 68 pixels spacing:
        0 = Home (Y ~68)
        1 = System Setup (Y ~136)
        2 = Patient Explorer (Y ~205)
        3 = Scheduling (Y ~273)
        4 = Lab Information (Y ~341)
        5 = Andrology (Y ~409)
        6 = Embryology (Y ~477)
        7 = Log Off (Y ~545)

    Args:
        main_window: The main eIVF window
        icon_index: Index of the icon to click (0-based)

    Returns:
        True if click successful, False otherwise
    """
    try:
        # Find the pvOutlookGroup pane (class_name="pvOutlookGroup", auto_id="100")
        sidebar_pane = main_window.child_window(
            class_name="pvOutlookGroup",
            auto_id="100",
            control_type="Pane"
        )

        if not sidebar_pane.exists(timeout=3):
            log_print("Could not find pvOutlookGroup sidebar pane")
            return False

        # Get the pane's rectangle
        rect = sidebar_pane.rectangle()
        pane_width = rect.width()

        log_print(f"Found sidebar pane: L={rect.left}, T={rect.top}, R={rect.right}, B={rect.bottom}")

        # Icon positions are fixed with ~68 pixels spacing
        # First icon starts at around Y=68, each subsequent icon is ~68 pixels below
        icon_spacing = 68
        first_icon_y = 68

        # Calculate Y position (center of the icon)
        click_x = pane_width // 2  # Center horizontally
        click_y = first_icon_y + (icon_index * icon_spacing)

        log_print(f"Clicking icon {icon_index} at relative position ({click_x}, {click_y})")

        # Click at the calculated position (relative to pane)
        sidebar_pane.click_input(coords=(click_x, click_y))

        time.sleep(1)
        return True

    except Exception as e:
        log_print(f"Error clicking sidebar icon: {str(e)}")
        return False


def click_patient_search_button():
    """
    Click the "Patient Search" button directly using AutomationId.

    Button properties from Inspect:
        - Name: "Patient Search"
        - AutomationId: "4"
        - ClassName: "ThunderRT6CommandButton"
        - ControlType: Button

    Returns:
        True if successful, False otherwise
    """
    log_print("Attempting to click Patient Search button directly...")

    try:
        # Get the main eIVF window
        app, main_window = get_eivf_main_window()

        if not main_window:
            log_print("Could not find main eIVF window")
            return False

        # Try to find the Patient Search button by AutomationId first (most reliable)
        try:
            patient_search_button = main_window.child_window(
                auto_id="4",
                control_type="Button",
                class_name="ThunderRT6CommandButton"
            )

            if patient_search_button.exists(timeout=3):
                log_print("Found Patient Search button by AutomationId")
                patient_search_button.click_input()
                log_print("Patient Search button clicked successfully")
                time.sleep(2)  # Increased wait time for window to appear
                return True
        except Exception as e:
            log_print(f"Could not find button by AutomationId: {e}")

        log_print("Patient Search button not found")
        return False

    except Exception as e:
        log_print(f"Error clicking Patient Search button: {str(e)}")
        return False


def open_patient_search_from_sidebar(main_window):
    """
    Click on "Patient Explorer" button in the left sidebar.
    Patient Explorer is the 3rd icon (index 2) in the sidebar.
    Returns: True if successful, False otherwise
    """
    log_print("Attempting to open Patient Explorer from sidebar...")

    # Patient Explorer is the 3rd icon (index 2)
    # Icons: 0=Home, 1=System Setup, 2=Patient Explorer, 3=Scheduling, etc.
    return click_sidebar_icon(main_window, icon_index=2)


def find_patient_search_window(return_window=False, max_wait=5):
    """
    Find patient search window/dialog and cache it for reuse.

    Tries multiple methods:
    1. As child of main eIVF window
    2. As top-level desktop window
    3. By searching all windows with different control types

    Args:
        return_window: If True, returns window object; if False, returns boolean
        max_wait: Maximum seconds to wait for window to appear

    Returns:
        If return_window=False: True if found, False otherwise
        If return_window=True: window object or None
    """
    # Check if we already have a cached window that's still valid
    cached_window = get_cached_patient_search_window()
    if cached_window:
        try:
            if cached_window.exists(timeout=0.5):
                log_print("Using cached Patient Search window")
                if return_window:
                    return cached_window
                return True
            else:
                log_print("Cached window no longer valid, searching again...")
                clear_cached_patient_search_window()
        except:
            clear_cached_patient_search_window()
    
    # ============================================================
    # SIMPLE DIRECT APPROACH using exact window properties:
    # <wnd app='eivf.exe' cls='ThunderRT6FormDC' title=' Patient Search ' />
    # ============================================================
    
    app, main_window = get_eivf_main_window()
    if not main_window:
        log_print("Could not find main eIVF window")
        return None if return_window else False

    # Wait for Patient Search window to appear
    for attempt in range(max_wait * 2):  # Check every 0.5 seconds
        log_print(f"Search attempt {attempt + 1}/{max_wait * 2}...")
        
        # PRIMARY METHOD: Direct window search by class and title
        # Title is ' Patient Search ' with leading/trailing spaces
        try:
            patient_search = main_window.child_window(
                title=" Patient Search ",
                class_name="ThunderRT6FormDC"
            )
            if patient_search.exists(timeout=0.5):
                log_print("Found Patient Search window (direct: cls='ThunderRT6FormDC' title=' Patient Search ')")
                set_cached_patient_search_window(patient_search)
                if return_window:
                    return patient_search
                return True
        except Exception as e:
            log_print(f"Direct search error: {str(e)[:50]}")
        
        # FALLBACK: Try with title regex to handle space variations
        try:
            patient_search = main_window.child_window(
                title_re=".*Patient.*Search.*",
                class_name="ThunderRT6FormDC"
            )
            if patient_search.exists(timeout=0.5):
                log_print("Found Patient Search window (regex match)")
                set_cached_patient_search_window(patient_search)
                if return_window:
                    return patient_search
                return True
        except:
            pass
        
        time.sleep(0.5)

    log_print(f"Patient Search window not found after waiting {max_wait} seconds")
    
    # Debug: List child windows
    try:
        log_print("Debug: Listing child windows...")
        child_windows = main_window.children(control_type="Window")
        for idx, child in enumerate(child_windows):
            try:
                child_text = child.window_text()
                child_class = child.element_info.class_name
                log_print(f"  Window {idx+1}: Title='{child_text}', Class='{child_class}'")
            except Exception as e:
                log_print(f"  Window {idx+1}: (could not read: {e})")
    except Exception as e:
        log_print(f"Debug: Could not list child windows: {e}")

    return None if return_window else False


def get_patient_search_window(max_wait=5):
    """
    Find and return the Patient Search window.
    Uses cached window if available and valid.

    Args:
        max_wait: Maximum seconds to wait for window to appear (default: 5)

    Returns: (app, window) tuple or (None, None) if not found
    """
    # Check if we have a cached window that's still valid
    cached_window = get_cached_patient_search_window()
    if cached_window:
        try:
            # Try multiple ways to validate the cached window
            is_valid = False
            try:
                # Method 1: Try exists() method
                is_valid = cached_window.exists(timeout=0.3)
            except:
                pass
            
            if not is_valid:
                try:
                    # Method 2: Try to get window_text() - if it works, window is still valid
                    win_text = cached_window.window_text()
                    if win_text and "patient" in win_text.lower():
                        is_valid = True
                        log_print(f"Cached window validated via window_text: '{win_text}'")
                except:
                    pass
            
            if not is_valid:
                try:
                    # Method 3: Try to check element_info
                    if cached_window.element_info:
                        is_valid = True
                        log_print("Cached window validated via element_info")
                except:
                    pass
            
            if is_valid:
                log_print("Using cached Patient Search window")
                app, _ = get_eivf_main_window()
                return app, cached_window
            else:
                log_print("Cached window no longer valid, searching again...")
                clear_cached_patient_search_window()
        except Exception as e:
            log_print(f"Error validating cached window: {str(e)[:50]}")
            clear_cached_patient_search_window()
    
    log_print("Searching for Patient Search window...")
    
    # ============================================================
    # SIMPLE DIRECT APPROACH using exact window properties:
    # <wnd app='eivf.exe' cls='ThunderRT6FormDC' title=' Patient Search ' />
    # ============================================================
    
    app, main_window = get_eivf_main_window()
    if not main_window:
        log_print("Could not find main eIVF window")
        return None, None

    # Get eIVF process ID
    eivf_pid = None
    try:
        eivf_pid = main_window.element_info.process_id
    except:
        pass

    # Wait for Patient Search window to appear
    for attempt in range(max_wait * 2):  # Check every 0.5 seconds
        log_print(f"Search attempt {attempt + 1}/{max_wait * 2}...")
        
        # PRIMARY METHOD: Direct window search by class and title
        # Title is ' Patient Search ' with leading/trailing spaces
        try:
            patient_search = main_window.child_window(
                title=" Patient Search ",
                class_name="ThunderRT6FormDC"
            )
            if patient_search.exists(timeout=0.5):
                log_print("Found Patient Search window (direct: cls='ThunderRT6FormDC' title=' Patient Search ')")
                set_cached_patient_search_window(patient_search)
                return app, patient_search
        except Exception as e:
            log_print(f"Direct search error: {str(e)[:50]}")
        
        # FALLBACK: Try with title regex to handle space variations
        try:
            patient_search = main_window.child_window(
                title_re=".*Patient.*Search.*",
                class_name="ThunderRT6FormDC"
            )
            if patient_search.exists(timeout=0.5):
                log_print("Found Patient Search window (regex match)")
                set_cached_patient_search_window(patient_search)
                return app, patient_search
        except:
            pass
        
        time.sleep(0.5)

    log_print(f"Patient Search window not found after waiting {max_wait} seconds")
    
    # Debug: List child windows
    try:
        log_print("Debug: Listing child windows...")
        child_windows = main_window.children(control_type="Window")
        for idx, child in enumerate(child_windows):
            try:
                child_text = child.window_text()
                child_class = child.element_info.class_name
                log_print(f"  Window {idx+1}: Title='{child_text}', Class='{child_class}'")
            except:
                log_print(f"  Window {idx+1}: (could not read properties)")
    except Exception as e:
        log_print(f"Debug: Could not list child windows: {e}")
    
    return None, None



def search_patient_by_phone_number_and_first_name_ctrl_id(phone_number, first_name, is_first=True):
    """
    Search patient by Phone Number and First Name using win32 backend.
    Uses control_id based element detection instead of coordinates.
    
    Args:
        phone_number: Phone number as string (e.g., "4155553333")
        first_name: The patient's first name
        is_first: If True, click Patient Explorer from sidebar first; if False, click Patient Search button first
    
    Returns:
        True if successful, False otherwise
    """
    log_print(f"\n=== Searching Patient by Phone Number: {phone_number} and First Name: {first_name} ===")
    
    try:
        # Step 0: Open Patient Search - different for first time vs subsequent times
        if is_first:
            # First time: Click Patient Explorer from sidebar
            log_print("First note: Clicking Patient Explorer from sidebar...")
            app_uia, main_window_uia = get_eivf_main_window()
            if not main_window_uia:
                log_print("Could not find eIVF window")
                return False
            if not open_patient_search_from_sidebar(main_window_uia):
                log_print("Failed to open Patient Explorer from sidebar")
                return False
            log_print("Patient Explorer opened from sidebar!")
            time.sleep(2)
        else:
            # Subsequent times: Click Patient Search button
            log_print("Subsequent note: Clicking Patient Search button...")
            if not click_patient_search_button():
                log_print("Failed to click Patient Search button")
                return False
            log_print("Patient Search button clicked!")
            time.sleep(2)
        
        # Connect using win32 backend for reliable element detection
        app = Application(backend="win32").connect(class_name="ThunderRT6MDIForm", title="eIVF")
        
        # Find the Patient Search window
        patient_search = app.window(class_name="ThunderRT6FormDC", title_re=".*Patient Search.*")
        patient_search.wait("visible", timeout=10)
        log_print(f"Found Patient Search window: {patient_search.window_text()}")
        
        # Step 1: Click Phone Number radio button (title="Phone  Number" with 2 spaces)
        log_print("Clicking Phone Number radio button...")
        phone_number_radio = patient_search.child_window(class_name="ThunderRT6OptionButton", title="Phone  Number")
        phone_number_radio.click()
        log_print("Phone Number radio button clicked")
        time.sleep(0.5)
        
        # Step 2: Find text box and type phone number (control_id=14)
        log_print(f"Entering phone number: {phone_number}")
        search_textbox = patient_search.child_window(class_name="ThunderRT6TextBox", control_id=14)
        search_textbox.set_focus()
        # Clear existing content with Ctrl+A + Backspace, then type new text
        search_textbox.type_keys("^a{BACKSPACE}" + phone_number)
        log_print("Phone number entered")
        time.sleep(0.5)
        
        # Step 3: Click search button (control_id=13)
        log_print("Clicking search button...")
        search_button = patient_search.child_window(class_name="ThunderRT6CommandButton", control_id=13)
        search_button.click()
        log_print("Search button clicked")
        time.sleep(0.5)
        
        # Re-fetch the Patient Search window after search to get fresh reference
        patient_search = app.window(class_name="ThunderRT6FormDC", title_re=".*Patient Search.*")
        patient_search.wait("visible", timeout=10)
        
        # Step 4: Click First Name radio button (control_id=18)
        log_print("Clicking First Name radio button...")
        first_name_radio = patient_search.child_window(class_name="ThunderRT6OptionButton", control_id=18)
        first_name_radio.click_input()
        log_print("First Name radio button clicked")
        time.sleep(0.5)
        
        # Step 5: Find text box and type first name (control_id=14)
        log_print(f"Entering first name: {first_name}")
        search_textbox = patient_search.child_window(class_name="ThunderRT6TextBox", control_id=14)
        search_textbox.set_focus()
        # Clear existing content with Ctrl+A + Backspace, then type new text
        search_textbox.type_keys("^a{BACKSPACE}" + first_name)
        log_print("First name entered")
        time.sleep(0.5)
        
        log_print("=== Patient Phone Number + First Name search completed successfully ===")


        # Click the search icon button (control_id=13, ClassName="ThunderRT6CommandButton")
        search_button = patient_search.child_window(class_name="ThunderRT6CommandButton", control_id=4)
        search_button.click()
        print("Clicked search button")
        time.sleep(0.5)
        return True
        
    except Exception as e:
        log_print(f"Error in patient search: {e}")
        import traceback
        traceback.print_exc()
        return False


def click_alert_ok_button():
    """
    Click the 'OK' button on the Patient Alert dialog that appears after selecting a patient.

    The Alert dialog has title starting with "Alert !!!" and contains patient allergy info.

    Returns:
        True if successful or no alert found, False if error
    """
    log_print("Checking for Patient Alert dialog...")

    try:
        # Get the main eIVF window
        app, main_window = get_eivf_main_window()

        if not main_window:
            log_print("Could not find main eIVF window")
            return False

        # Look for Alert dialog - title starts with "Alert !!!"
        try:
            alert_window = main_window.child_window(
                title_re=".*Alert.*",
                control_type="Window"
            )

            if alert_window.exists(timeout=3):
                log_print("Found Alert dialog")

                # Find and click OK button
                ok_button = alert_window.child_window(
                    title="OK",
                    control_type="Button"
                )

                if ok_button.exists(timeout=2):
                    ok_button.click_input()
                    log_print("Alert OK button clicked successfully")
                    time.sleep(0.5)
                    return True
                else:
                    # Try finding by class
                    buttons = alert_window.children(control_type="Button")
                    for btn in buttons:
                        try:
                            if "ok" in btn.window_text().lower():
                                btn.click_input()
                                log_print("Alert OK button clicked")
                                time.sleep(0.5)
                                return True
                        except:
                            continue

                    log_print("OK button not found in Alert dialog")
                    return False
            else:
                log_print("No Alert dialog found - continuing")
                return True  # No alert is OK

        except Exception as e:
            log_print(f"No Alert dialog: {e}")
            return True  # No alert is OK

    except Exception as e:
        log_print(f"Error handling Alert dialog: {str(e)}")
        return False



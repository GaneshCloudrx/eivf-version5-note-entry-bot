"""
Patient search module - handles searching for patients in eIVF
"""
import time
from pywinauto import Application, Desktop

import modules.helper as helper


def get_desktop():
    """Get Desktop instance with UIA backend."""
    return Desktop(backend="uia")


def get_eivf_main_window():
    """
    Find and connect to the main eIVF window.
    Returns: (app, main_window) tuple or (None, None) if not found
    """
    desktop = get_desktop()

    for win in desktop.windows():
        try:
            win_title = win.window_text()
            win_class = win.element_info.class_name
            if win_title.lower() == "eivf" and win_class == "ThunderRT6MDIForm":
                process_id = win.element_info.process_id
                helper.log_print(f"Found main eIVF window (PID: {process_id})")
                app = Application(backend="uia").connect(process=process_id)
                main_window = app.window(title=win_title, class_name="ThunderRT6MDIForm")
                return app, main_window
        except:
            pass

    return None, None


def click_sidebar_icon(main_window, icon_index):
    """
    Click on a specific icon in the sidebar pane.
    Icons: 0=Home, 1=System Setup, 2=Patient Explorer, 3=Scheduling, etc.
    """
    try:
        # Step 3: Check for .NET error dialog before adding note
        #helper.check_and_close_dotnet_error_dialog()
        
        sidebar_pane = main_window.child_window(
            class_name="pvOutlookGroup",
            auto_id="100",
            control_type="Pane"
        )

        if not sidebar_pane.exists(timeout=3):
            helper.log_print("Could not find sidebar pane")
            return False

        rect = sidebar_pane.rectangle()
        icon_spacing = 68
        first_icon_y = 68
        click_x = rect.width() // 2
        click_y = first_icon_y + (icon_index * icon_spacing)

        helper.log_print(f"Clicking sidebar icon {icon_index}")
        sidebar_pane.click_input(coords=(click_x, click_y))
        time.sleep(1)

        return True

    except Exception as e:
        helper.log_print(f"Error clicking sidebar icon: {str(e)}")
        return False


def click_patient_search_button():
    """Click the Patient Search button directly."""
    helper.log_print("Clicking Patient Search button...")

    try:
        app, main_window = get_eivf_main_window()
        if not main_window:
            helper.log_print("Could not find main eIVF window")
            raise Exception("eivf_window_not_found")

        try:
            patient_search_button = main_window.child_window(
                auto_id="4",
                control_type="Button",
                class_name="ThunderRT6CommandButton"
            )

            if patient_search_button.exists(timeout=3):
                patient_search_button.click_input()
                helper.log_print("Patient Search button clicked")
                time.sleep(3)
                return True
        except Exception as e:
            helper.log_print(f"Could not find button: {e}")

        helper.log_print("Patient Search button not found")
        return False

    except Exception as e:
        helper.log_print(f"Error clicking Patient Search button: {str(e)}")
        return False


def open_patient_search_from_pane(main_window, clinic_name_sf=None):
    """
    Click on Patient Explorer based on clinic type.
    For IVFMD: Use sidebar icon method
    For others: Use relative coordinates method
    """
    helper.log_print(f"Opening Patient Explorer for clinic: {clinic_name_sf}...")
    
    try:
        # Check if clinic is IVFMD
        if clinic_name_sf and clinic_name_sf == "IVFMD":
            helper.log_print("Using sidebar icon method for IVFMD clinic")
            result = click_sidebar_icon(main_window, 2)  # Patient Explorer is icon index 2
            if not result:
                raise Exception("Failed to click sidebar icon")
            return True
        else:
            helper.log_print("Using coordinate-based method for non-IVFMD clinic")
            # Reconnect using win32 backend
            app = Application(backend="win32").connect(class_name="ThunderRT6MDIForm", title="eIVF")
            main_window_win32 = app.window(class_name="ThunderRT6MDIForm", title="eIVF")
            
            # Calculate relative coordinates from absolute position (181, 87)
            rect = main_window_win32.rectangle()
            click_x = 181 - rect.left
            click_y = 87 - rect.top
            
            helper.log_print(f"Clicking at relative coords ({click_x}, {click_y})")
            main_window_win32.click_input(coords=(click_x, click_y))
            time.sleep(1)
            helper.log_print("Patient Explorer clicked successfully")
            return True
        
    except Exception as e:
        error_str = str(e).lower()
        if "could not find" in error_str or "not found" in error_str or "timed out" in error_str:
            helper.log_print(f"Error clicking Patient Explorer: {e}")
            raise Exception("eivf_window_not_found")
        helper.log_print(f"Error clicking Patient Explorer: {e}")
        return False


def search_patient_by_phone_number_and_first_name_ctrl_id(phone_number, first_name, is_first=True, clinic_name_sf=None):
    """
    Search patient by Phone Number and First Name using win32 backend.
    
    Args:
        phone_number: Phone number string
        first_name: Patient's first name
        is_first: If True, click Patient Explorer from sidebar; else click Patient Search button
        clinic_name_sf: Clinic name from Salesforce (used to determine click method)
    
    Returns:
        True if successful, False otherwise
    """
    helper.log_print(f"\n=== Searching: Phone={phone_number}, FirstName={first_name} ===")
    
    try:
        # Step 0: Open Patient Search
        if is_first:
            helper.log_print("First note: Opening Patient Explorer from sidebar...")
            app_uia, main_window_uia = get_eivf_main_window()
            if not main_window_uia:
                helper.log_print("Could not find eIVF window")
                return False
            if not open_patient_search_from_pane(main_window_uia, clinic_name_sf):
                helper.log_print("Failed to open Patient Explorer")
                return False
            time.sleep(2)
        else:
            helper.log_print("Subsequent note: Clicking Patient Search button...")
            if not click_patient_search_button():
                helper.log_print("Failed to click Patient Search button")
                return False
            time.sleep(2)
        
        # Connect using win32 backend
        app = Application(backend="win32").connect(class_name="ThunderRT6MDIForm", title="eIVF")
        patient_search = app.window(class_name="ThunderRT6FormDC", title_re=".*Patient Search.*")
        patient_search.wait("visible", timeout=10)
        helper.log_print(f"Found Patient Search window")

        
        
        # Step 1: Click Phone Number radio button
        phone_number_radio = patient_search.child_window(class_name="ThunderRT6OptionButton", title="Phone  Number")
        phone_number_radio.click()
        time.sleep(0.5)

        # Step 1.5: Click search button
        search_button = patient_search.child_window(class_name="ThunderRT6CommandButton", control_id=1)
        search_button.click_input()
        time.sleep(0.5)
        
        # Step 2: Enter phone number
        search_textbox = patient_search.child_window(class_name="ThunderRT6TextBox", control_id=14)
        search_textbox.set_focus()
        search_textbox.type_keys("^a{BACKSPACE}" + phone_number)
        time.sleep(0.5)
        
        # Step 3: Click search button
        search_button = patient_search.child_window(class_name="ThunderRT6CommandButton", control_id=13)
        search_button.click()
        time.sleep(0.5)
        
        # Re-fetch window after search
        patient_search = app.window(class_name="ThunderRT6FormDC", title_re=".*Patient Search.*")
        patient_search.wait("visible", timeout=10)
        
        # Step 4: Click First Name radio button
        first_name_radio = patient_search.child_window(class_name="ThunderRT6OptionButton", control_id=18)
        first_name_radio.click_input()
        time.sleep(0.5)
        
        # Step 5: Enter first name
        search_textbox = patient_search.child_window(class_name="ThunderRT6TextBox", control_id=14)
        search_textbox.set_focus()
        search_textbox.type_keys("^a{BACKSPACE}" + first_name)
        time.sleep(0.5)
        
        # Step 5a: Navigate through fields - Tab, Tab, Down Arrow
        # Send keys to the patient_search window instead of specific textbox
        helper.log_print("Navigating through search fields...")
        patient_search.type_keys("{TAB}")
        time.sleep(1)
        
        patient_search.type_keys("{TAB}")
        time.sleep(1)
        
        patient_search.type_keys("{DOWN}")
        time.sleep(1)
        
        
        # Step 6: Click search to select patient
        search_button = patient_search.child_window(class_name="ThunderRT6CommandButton", control_id=4)
        search_button.click()
        time.sleep(0.5)
        
        helper.log_print("=== Patient search completed ===")
        return True
        
    except Exception as e:
        error_msg = str(e).lower()
        helper.log_print(f"Error in patient search: {e}")
        import traceback
        traceback.print_exc()
        # Check if it's a timeout error
        if "timeout" in error_msg or "timed out" in error_msg:
            # Raise a special exception for timeout that can be caught to skip clinic
            raise Exception("patient_search_timeout")
        return False


def click_alert_ok_button():
    """Click OK button on Patient Alert dialog if it appears."""
    helper.log_print("Checking for Patient Alert dialog...")

    try:
        app = Application(backend="win32").connect(class_name="ThunderRT6MDIForm", title="eIVF")
        alert_window = app.window(title_re=".*Alert.*")
        alert_window.wait("visible", timeout=10)
        helper.log_print(f"Found Alert window")

        time.sleep(0.5)
        alert_window.set_focus()
        time.sleep(0.3)

        ok_button = alert_window.child_window(title="OK", class_name="ThunderRT6CommandButton")
        ok_button.set_focus()
        time.sleep(0.2)
        ok_button.click_input()
        helper.log_print("Clicked OK on Alert")
        return True

    except Exception as e:
        helper.log_print(f"Alert dialog not found or error: {str(e)}")
        return False

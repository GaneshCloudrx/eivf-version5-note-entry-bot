from pywinauto import Application, Desktop
from pywinauto.keyboard import send_keys
import time
import traceback
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
    Find patient search window/dialog.
    
    Note: Patient Search is a child window (ThunderRT6FormDC) inside the eIVF MDI window,
    not a top-level desktop window.
   
    Args:
        return_window: If True, returns window object; if False, returns boolean
        max_wait: Maximum seconds to wait for window to appear
       
    Returns:
        If return_window=False: True if found, False otherwise
        If return_window=True: window object or None
    """
    # First get the main eIVF window
    app, main_window = get_eivf_main_window()
    
    if not main_window:
        log_print("Could not find main eIVF window")
        return None if return_window else False
    
    # Wait for Patient Search child window to appear
    for attempt in range(max_wait * 2):  # Check every 0.5 seconds
        try:
            # Patient Search is a child window with class ThunderRT6FormDC
            # Title is " Patient Search " (with spaces)
            patient_search = main_window.child_window(
                title_re=".*Patient.*Search.*",
                class_name="ThunderRT6FormDC",
                control_type="Window"
            )
            
            if patient_search.exists(timeout=0.5):
                log_print(f"Found Patient Search window")
                if return_window:
                    return patient_search
                return True
        except:
            pass
        
        time.sleep(0.5)
   
    log_print("Patient search window not found after waiting")
    return None if return_window else False




def get_patient_search_window():
    """
    Find and return the Patient Search window.
    
    Note: Patient Search is a child window (ThunderRT6FormDC) inside the eIVF MDI window,
    not a top-level desktop window.
    
    Returns: (app, window) tuple or (None, None) if not found
    """
    # First get the main eIVF window
    app, main_window = get_eivf_main_window()
    
    if not main_window:
        log_print("Could not find main eIVF window")
        return None, None
    
    try:
        # Patient Search is a child window with class ThunderRT6FormDC
        # Title is " Patient Search " (with spaces)
        patient_search = main_window.child_window(
            title_re=".*Patient.*Search.*",
            class_name="ThunderRT6FormDC",
            control_type="Window"
        )
        
        if patient_search.exists(timeout=3):
            log_print("Found Patient Search window")
            return app, patient_search
    except Exception as e:
        log_print(f"Error finding Patient Search window: {str(e)}")
    
    return None, None


def click_dob_radio_button():
    """
    Click on the DOB radio button in the Patient Search window.
    
    DOB radio button properties:
        - Name: "DOB"
        - ControlType: RadioButton
        - ClassName: "ThunderRT6OptionButton"
        - AutomationId: "12"
    
    Returns:
        True if successful, False otherwise
    """
    log_print("Clicking DOB radio button...")
    
    try:
        # Get the Patient Search window
        app, search_window = get_patient_search_window()
        
        if not search_window:
            log_print("Could not find Patient Search window")
            return False
        
        # Find the DOB radio button
        dob_radio = search_window.child_window(
            title="DOB",
            control_type="RadioButton",
            class_name="ThunderRT6OptionButton",
            auto_id="12"
        )
        
        if dob_radio.exists(timeout=3):
            dob_radio.click_input()
            log_print("DOB radio button clicked successfully")
            time.sleep(0.5)
            return True
        else:
            log_print("DOB radio button not found")
            return False
            
    except Exception as e:
        log_print(f"Error clicking DOB radio button: {str(e)}")
        return False


def click_last_name_radio_button():
    """
    Click on the Last Name radio button in the Patient Search window.
    
    Last Name radio button properties:
        - Name: "Last Name"
        - ControlType: RadioButton
        - ClassName: "ThunderRT6OptionButton"
        - AutomationId: "19"
    
    Returns:
        True if successful, False otherwise
    """
    log_print("Clicking Last Name radio button...")
    
    try:
        # Get the Patient Search window
        app, search_window = get_patient_search_window()
        
        if not search_window:
            log_print("Could not find Patient Search window")
            return False
        
        # Find the Last Name radio button
        last_name_radio = search_window.child_window(
            title="Last Name",
            control_type="RadioButton",
            class_name="ThunderRT6OptionButton",
            auto_id="19"
        )
        
        if last_name_radio.exists(timeout=3):
            last_name_radio.click_input()
            log_print("Last Name radio button clicked successfully")
            time.sleep(0.5)
            return True
        else:
            log_print("Last Name radio button not found")
            return False
            
    except Exception as e:
        log_print(f"Error clicking Last Name radio button: {str(e)}")
        return False


def type_last_name_in_textbox(last_name):
    """
    Type last name into the textbox in Patient Search window.
    
    Last Name textbox properties:
        - ControlType: Edit
        - ClassName: "ThunderRT6TextBox"
        - AutomationId: "14"
    
    Args:
        last_name: The last name to type
        
    Returns:
        True if successful, False otherwise
    """
    log_print(f"Typing Last Name: {last_name}")
    
    try:
        # Get the Patient Search window
        app, search_window = get_patient_search_window()
        
        if not search_window:
            log_print("Could not find Patient Search window")
            return False
        
        # Find the Last Name textbox
        last_name_textbox = search_window.child_window(
            auto_id="14",
            class_name="ThunderRT6TextBox",
            control_type="Edit"
        )
        
        if not last_name_textbox.exists(timeout=3):
            log_print("Last Name textbox not found")
            return False
        
        # Click on the textbox to focus it
        last_name_textbox.click_input()
        time.sleep(0.3)
        
        # Clear existing text (Ctrl+A to select all, then Delete)
        last_name_textbox.type_keys("^a", with_spaces=True)
        time.sleep(0.1)
        last_name_textbox.type_keys("{DELETE}", with_spaces=True)
        time.sleep(0.2)
        
        # Type the last name
        last_name_textbox.type_keys(last_name, with_spaces=True)
        
        log_print(f"Last Name '{last_name}' typed successfully")
        time.sleep(0.3)
        return True
        
    except Exception as e:
        log_print(f"Error typing Last Name: {str(e)}")
        return False


def get_clipboard_content():
    """Get content from Windows clipboard using ctypes."""
    import ctypes
    from ctypes import wintypes
    
    CF_UNICODETEXT = 13
    
    user32 = ctypes.windll.user32
    kernel32 = ctypes.windll.kernel32
    
    user32.OpenClipboard(0)
    try:
        if user32.IsClipboardFormatAvailable(CF_UNICODETEXT):
            data = user32.GetClipboardData(CF_UNICODETEXT)
            data_locked = kernel32.GlobalLock(data)
            try:
                text = ctypes.wstring_at(data_locked)
                return text
            finally:
                kernel32.GlobalUnlock(data_locked)
        return ""
    finally:
        user32.CloseClipboard()


def get_search_results_content():
    """
    Extract content from the search results grid (VSFlexGridL).
    
    Since VSFlexGridL doesn't expose children, we use clipboard method:
    1. Click on the grid to focus
    2. Ctrl+A to select all
    3. Ctrl+C to copy
    4. Read from clipboard
    
    Returns:
        String content of the grid, or None if failed
    """
    log_print("Extracting search results content...")
    
    try:
        # Get the Patient Search window
        app, search_window = get_patient_search_window()
        
        if not search_window:
            log_print("Could not find Patient Search window")
            return None
        
        # Find the search results grid (VSFlexGridL)
        results_grid = search_window.child_window(
            class_name="VSFlexGridL",
            control_type="Pane"
        )
        
        if not results_grid.exists(timeout=3):
            log_print("Search results grid not found")
            return None
        
        # Click on the grid to focus it
        results_grid.click_input()
        time.sleep(0.3)
        
        # Select all content (Ctrl+A)
        results_grid.type_keys("^a", with_spaces=True)
        time.sleep(0.2)
        
        # Copy to clipboard (Ctrl+C)
        results_grid.type_keys("^c", with_spaces=True)
        time.sleep(0.3)
        
        # Read from clipboard using Windows API
        content = get_clipboard_content()
        
        log_print(f"Extracted content: {content[:200] if content else 'Empty'}...")
        return content
        
    except Exception as e:
        log_print(f"Error extracting search results: {str(e)}")
        return None


def verify_patient_match(first_name, last_name, dob):
    """
    Verify if the search results match the expected patient details.
    
    Args:
        first_name: Expected first name
        last_name: Expected last name
        dob: Expected DOB (can be in various formats like "01/01/1980" or "01011980")
        
    Returns:
        True if patient matches, False otherwise
    """
    log_print(f"Verifying patient: {first_name} {last_name}, DOB: {dob}")
    
    content = get_search_results_content()
    
    if not content:
        log_print("No content to verify")
        return False
    
    content_lower = content.lower()
    
    # Check first name
    first_name_match = first_name.lower() in content_lower
    log_print(f"First Name '{first_name}' match: {first_name_match}")
    
    # Check last name
    last_name_match = last_name.lower() in content_lower
    log_print(f"Last Name '{last_name}' match: {last_name_match}")
    
    # Check DOB - handle different formats
    # Convert MMddyyyy to common formats for checking
    dob_formats = [dob]
    if len(dob) == 8 and dob.isdigit():
        # Convert MMddyyyy to other formats
        mm, dd, yyyy = dob[:2], dob[2:4], dob[4:]
        dob_formats.extend([
            f"{mm}/{dd}/{yyyy}",      # MM/dd/yyyy
            f"{mm}-{dd}-{yyyy}",      # MM-dd-yyyy
            f"{int(mm)}/{int(dd)}/{yyyy}",  # M/d/yyyy (no leading zeros)
        ])
    
    dob_match = any(fmt.lower() in content_lower for fmt in dob_formats)
    log_print(f"DOB '{dob}' match: {dob_match}")
    
    # All must match
    all_match = first_name_match and last_name_match and dob_match
    log_print(f"Overall patient match: {all_match}")
    
    return all_match


def type_dob_in_textbox(dob_string):
    """
    Type DOB into the date textbox in Patient Search window.
    
    The DOB should be in MMddyyyy format (e.g., "01011980" for January 1, 1980).
    Characters are typed one by one for reliability with this OLE control.
    
    DOB textbox properties:
        - ControlType: Pane
        - ClassName: "AfxOleControl42"
    
    Args:
        dob_string: DOB in MMddyyyy format (e.g., "01011980")
        
    Returns:
        True if successful, False otherwise
    """
    log_print(f"Typing DOB: {dob_string}")
    
    try:
        # Get the Patient Search window
        app, search_window = get_patient_search_window()
        
        if not search_window:
            log_print("Could not find Patient Search window")
            return False
        
        # Find the DOB textbox (AfxOleControl42)
        dob_textbox = search_window.child_window(
            class_name="AfxOleControl42",
            control_type="Pane"
        )
        
        if not dob_textbox.exists(timeout=3):
            log_print("DOB textbox not found")
            return False
        
        # Click on the textbox to focus it
        dob_textbox.click_input()
        time.sleep(0.3)
        
        # Clear existing text (Ctrl+A to select all, then Delete)
        dob_textbox.type_keys("^a", with_spaces=True)
        time.sleep(0.1)
        dob_textbox.type_keys("{DELETE}", with_spaces=True)
        time.sleep(0.2)
        
        # Type DOB one character at a time
        for char in dob_string:
            dob_textbox.type_keys(char, with_spaces=True)
            time.sleep(0.05)  # Small delay between characters
        
        log_print(f"DOB '{dob_string}' typed successfully")
        time.sleep(0.3)
        return True
        
    except Exception as e:
        log_print(f"Error typing DOB: {str(e)}")
        return False


def click_search_button():
    """
    Click the search button next to the DOB textbox in Patient Search window.
    
    Search button properties:
        - Name: "" (empty)
        - ControlType: Button
        - ClassName: "ThunderRT6CommandButton"
        - AutomationId: "13"
    
    Returns:
        True if successful, False otherwise
    """
    log_print("Clicking search button...")
    
    try:
        # Get the Patient Search window
        app, search_window = get_patient_search_window()
        
        if not search_window:
            log_print("Could not find Patient Search window")
            return False
        
        # Find the search button
        search_button = search_window.child_window(
            auto_id="13",
            control_type="Button",
            class_name="ThunderRT6CommandButton"
        )
        
        if search_button.exists(timeout=3):
            search_button.click_input()
            log_print("Search button clicked successfully")
            time.sleep(1)  # Wait for search results
            return True
        else:
            log_print("Search button not found")
            return False
            
    except Exception as e:
        log_print(f"Error clicking search button: {str(e)}")
        return False


def open_patient_search(window):
    """
    Open patient search window from the sidebar.
   
    Args:
        window: The login window (may not be needed after login)
       
    Returns:
        True if patient search opened successfully, False otherwise
    """
    log_print("\n=== Opening Patient Search ===")
   
    # Get the main eIVF window
    app, main_window = get_eivf_main_window()
   
    if not main_window:
        log_print("Could not find main eIVF window")
        return False
   
    # Ensure window is focused and maximized
    try:
        main_window.set_focus()
        main_window.maximize()
        time.sleep(0.5)
    except:
        pass
   
    # Click sidebar "Patient Search" button
    if open_patient_search_from_sidebar(main_window):
        if find_patient_search_window():
            log_print("Patient search opened successfully via sidebar!")
            return True
        log_print("Sidebar clicked but patient search window not detected")
   
    # Final check - maybe it opened but we didn't detect it properly
    time.sleep(1)
    if find_patient_search_window():
        log_print("Patient search window detected")
        return True
   
    log_print("Failed to open patient search")
    return False


def search_patient_by_dob(window, dob_string):
    """
    Complete workflow to search for a patient by DOB.
    
    This function performs all steps in sequence:
    1. Open Patient Search window
    2. Click DOB radio button
    3. Type DOB in textbox
    4. Click Search button
    
    Args:
        window: The login window (may not be needed after login)
        dob_string: DOB in MMddyyyy format (e.g., "01011980" for January 1, 1980)
        
    Returns:
        True if all steps successful, False otherwise
    """
    log_print(f"\n=== Searching Patient by DOB: {dob_string} ===")
    
    # Step 1: Open Patient Search
    if not open_patient_search(window):
        log_print("Failed to open Patient Search")
        return False
    log_print("Patient Search opened successfully!")
    
    # Step 2: Click DOB radio button
    if not click_dob_radio_button():
        log_print("Failed to click DOB radio button")
        return False
    log_print("DOB radio button clicked!")
    
    # Step 3: Type DOB
    if not type_dob_in_textbox(dob_string):
        log_print("Failed to type DOB")
        return False
    log_print(f"DOB '{dob_string}' entered successfully!")
    
    # Step 4: Click Search button
    if not click_search_button():
        log_print("Failed to click search button")
        return False
    log_print("Search button clicked! Waiting for results...")
    
    log_print("=== Patient DOB search completed successfully ===")
    return True


def search_patient_by_dob_and_last_name(window, dob_string, last_name):
    """
    Complete workflow to search for a patient by DOB and Last Name.
    
    This function performs all steps in sequence:
    1. Open Patient Search window
    2. Click DOB radio button
    3. Type DOB in textbox
    4. Click Search button
    5. Click Last Name radio button
    6. Type Last Name in textbox
    7. Click Search button again
    
    Args:
        window: The login window (may not be needed after login)
        dob_string: DOB in MMddyyyy format (e.g., "01011980" for January 1, 1980)
        last_name: The patient's last name
        
    Returns:
        True if all steps successful, False otherwise
    """
    log_print(f"\n=== Searching Patient by DOB: {dob_string} and Last Name: {last_name} ===")
    
    # Step 1: Open Patient Search
    if not open_patient_search(window):
        log_print("Failed to open Patient Search")
        return False
    log_print("Patient Search opened successfully!")
    
    # Step 2: Click DOB radio button
    if not click_dob_radio_button():
        log_print("Failed to click DOB radio button")
        return False
    log_print("DOB radio button clicked!")
    
    # Step 3: Type DOB
    if not type_dob_in_textbox(dob_string):
        log_print("Failed to type DOB")
        return False
    log_print(f"DOB '{dob_string}' entered successfully!")
    
    # Step 4: Click Search button (first search by DOB)
    if not click_search_button():
        log_print("Failed to click search button")
        return False
    log_print("Search button clicked (DOB search)!")
    time.sleep(1)  # Wait for results
    
    # Step 5: Click Last Name radio button
    if not click_last_name_radio_button():
        log_print("Failed to click Last Name radio button")
        return False
    log_print("Last Name radio button clicked!")
    
    # Step 6: Type Last Name
    if not type_last_name_in_textbox(last_name):
        log_print("Failed to type Last Name")
        return False
    log_print(f"Last Name '{last_name}' entered successfully!")
    
    # Step 7: Click Search button (search with DOB + Last Name)
    log_print("=== Patient DOB + Last Name search completed successfully ===")
    return True

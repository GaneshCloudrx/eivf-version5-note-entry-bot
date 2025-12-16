from pywinauto import Application, Desktop, mouse
from pywinauto.keyboard import send_keys
import time
import re
from modules.utils import log_print


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
    Find patient search window/dialog.

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
    # Get eIVF process ID to filter windows
    app, main_window = get_eivf_main_window()
    eivf_pid = None
    if main_window:
        try:
            eivf_pid = main_window.element_info.process_id
        except:
            pass

    # Wait for Patient Search window to appear
    for attempt in range(max_wait * 2):  # Check every 0.5 seconds
        # Method 1: Try as top-level desktop window FIRST (most likely after button click)
        # But only match windows from the same eIVF process
        try:
            desktop = get_desktop()
            for win in desktop.windows():
                try:
                    win_title = win.window_text()
                    win_class = win.element_info.class_name
                    win_pid = win.element_info.process_id
                    
                    # Only check windows from eIVF process
                    if eivf_pid:
                        if win_pid != eivf_pid:
                            continue
                    else:
                        log_print(f"Warning: eIVF PID not available, skipping process filter")
                    
                    # Must have ThunderRT6FormDC class AND patient/search in title
                    # Also verify it's not a false match (like Cursor editor)
                    if "ThunderRT6FormDC" in win_class:
                        title_lower = win_title.lower()
                        if "patient" in title_lower and "search" in title_lower:
                            # Additional validation: exclude common false matches
                            if "cursor" not in title_lower and "chrome" not in title_lower and ".py" not in title_lower:
                                log_print(f"Found Patient Search window (method 1: desktop by title+class): '{win_title}', PID: {win_pid}, eIVF PID: {eivf_pid}")
                                if return_window:
                                    return win
                                return True
                            else:
                                log_print(f"Skipping false match: '{win_title}' (contains cursor/chrome/.py)")
                except:
                    continue
        except Exception as e:
            pass

        # Method 2: Try desktop windows by class name only (from eIVF process)
        try:
            desktop = get_desktop()
            for win in desktop.windows():
                try:
                    win_pid = win.element_info.process_id
                    # Only check windows from eIVF process
                    if eivf_pid:
                        if win_pid != eivf_pid:
                            continue
                    
                    win_class = win.element_info.class_name
                    if "ThunderRT6FormDC" in win_class:
                        win_title = win.window_text()
                        title_lower = win_title.lower()
                        if "patient" in title_lower and "search" in title_lower:
                            # Additional validation: exclude common false matches
                            if "cursor" not in title_lower and "chrome" not in title_lower and ".py" not in title_lower:
                                log_print(f"Found Patient Search window (method 2: desktop by class): '{win_title}', PID: {win_pid}")
                                if return_window:
                                    return win
                                return True
                            else:
                                log_print(f"Skipping false match: '{win_title}' (contains cursor/chrome/.py)")
                except:
                    continue
        except:
            pass

        # Method 3: Try as child of main window
        app, main_window = get_eivf_main_window()
        if main_window:
            try:
                # Try with title regex and class name
                patient_search = main_window.child_window(
                    title_re=".*\\s*Patient\\s+Search\\s*.*",
                    class_name="ThunderRT6FormDC",
                    control_type="Window"
                )

                if patient_search.exists(timeout=0.5):
                    log_print(f"Found Patient Search window (method 3: child window)")
                    if return_window:
                        return patient_search
                    return True
            except:
                pass

            # Method 4: Try with just class name and check title
            try:
                patient_search = main_window.child_window(
                    class_name="ThunderRT6FormDC",
                    control_type="Window"
                )
                
                if patient_search.exists(timeout=0.5):
                    try:
                        win_text = patient_search.window_text()
                        if "patient" in win_text.lower() and "search" in win_text.lower():
                            log_print(f"Found Patient Search window (method 4: child by class): '{win_text}'")
                            if return_window:
                                return patient_search
                            return True
                    except:
                        pass
            except:
                pass

            # Method 5: Search all child windows
            try:
                child_windows = main_window.children(control_type="Window")
                for child in child_windows:
                    try:
                        child_text = child.window_text()
                        child_class = child.element_info.class_name
                        if ("patient" in child_text.lower() and "search" in child_text.lower()) and "ThunderRT6FormDC" in child_class:
                            log_print(f"Found Patient Search window (method 5: iterate children): '{child_text}'")
                            if return_window:
                                return child
                            return True
                    except:
                        continue
            except:
                pass

            # Method 6: Try different control types (Dialog, Pane, etc.)
            for control_type in ["Dialog", "Pane", "Window"]:
                try:
                    patient_search = main_window.child_window(
                        title_re=".*Patient.*Search.*",
                        control_type=control_type
                    )
                    if patient_search.exists(timeout=0.3):
                        try:
                            win_text = patient_search.window_text()
                            if "patient" in win_text.lower() and "search" in win_text.lower():
                                log_print(f"Found Patient Search window (method 6: {control_type}): '{win_text}'")
                                if return_window:
                                    return patient_search
                                return True
                        except:
                            pass
                except:
                    pass

        time.sleep(0.5)

    # Debug: List all windows to help diagnose
    log_print("Debug: Listing windows after search failed...")
    app, main_window = get_eivf_main_window()
    if main_window:
        try:
            log_print("Child windows of main window:")
            child_windows = main_window.children(control_type="Window")
            log_print(f"Found {len(child_windows)} child windows")
            for idx, child in enumerate(child_windows):
                try:
                    child_text = child.window_text()
                    child_class = child.element_info.class_name
                    log_print(f"  Window {idx+1}: Title='{child_text}', Class='{child_class}'")
                except Exception as e:
                    log_print(f"  Window {idx+1}: (could not read properties: {e})")
        except Exception as e:
            log_print(f"Debug: Could not list child windows: {e}")
    
    # Also list all desktop windows (show all, not just matches)
    try:
        log_print("All desktop windows (showing all):")
        desktop = get_desktop()
        desktop_windows = desktop.windows()
        log_print(f"Found {len(desktop_windows)} desktop windows")
        for idx, win in enumerate(desktop_windows):
            try:
                win_title = win.window_text()
                win_class = win.element_info.class_name
                # Show all windows, highlight potential matches
                if "patient" in win_title.lower() or "search" in win_title.lower() or "ThunderRT6FormDC" in win_class:
                    log_print(f"  *** Window {idx+1}: Title='{win_title}', Class='{win_class}' ***")
                else:
                    log_print(f"  Window {idx+1}: Title='{win_title}', Class='{win_class}'")
            except Exception as e:
                log_print(f"  Window {idx+1}: (could not read: {e})")
    except Exception as e:
        log_print(f"Debug: Could not list desktop windows: {e}")

    log_print("Patient search window not found after waiting")
    return None if return_window else False


def get_patient_search_window(max_wait=5):
    """
    Find and return the Patient Search window.

    Args:
        max_wait: Maximum seconds to wait for window to appear (default: 5)

    Returns: (app, window) tuple or (None, None) if not found
    """
    log_print("Searching for Patient Search window from main window...")
    app, main_window = get_eivf_main_window()

    if not main_window:
        log_print("Could not find main eIVF window")
        return None, None

    # Get eIVF process ID to filter windows
    eivf_pid = None
    try:
        eivf_pid = main_window.element_info.process_id
    except:
        pass

    # Wait for Patient Search window to appear with retry logic
    for attempt in range(max_wait * 2):  # Check every 0.5 seconds
        # Method 1: Try desktop windows first (from eIVF process)
        try:
            desktop = get_desktop()
            for win in desktop.windows():
                try:
                    win_pid = win.element_info.process_id
                    # Only check windows from eIVF process
                    if eivf_pid and win_pid != eivf_pid:
                        continue
                    
                    win_title = win.window_text()
                    win_class = win.element_info.class_name
                    if "ThunderRT6FormDC" in win_class:
                        title_lower = win_title.lower()
                        if "patient" in title_lower and "search" in title_lower:
                            # Additional validation: exclude common false matches
                            if "cursor" not in title_lower and "chrome" not in title_lower and ".py" not in title_lower:
                                log_print(f"Found Patient Search window (method 1: desktop): '{win_title}', PID: {win_pid}")
                                return app, win
                            else:
                                log_print(f"Skipping false match in get_patient_search_window: '{win_title}'")
                except:
                    continue
        except:
            pass

        # Method 2: Try as child of main window
        try:
            # Try with title regex and class name
            # Regex matches: optional spaces + "Patient" + one or more spaces + "Search" + optional spaces
            patient_search = main_window.child_window(
                title_re=".*\\s*Patient\\s+Search\\s*.*",
                class_name="ThunderRT6FormDC",
                control_type="Window"
            )

            if patient_search.exists(timeout=0.5):
                log_print("Found Patient Search window (method 2: child window)")
                return app, patient_search
        except Exception as e:
            pass  # Continue trying
        
        # Method 2: Try with just class name and check title
        try:
            patient_search = main_window.child_window(
                class_name="ThunderRT6FormDC",
                control_type="Window"
            )
            
            if patient_search.exists(timeout=0.5):
                try:
                    win_text = patient_search.window_text()
                    if "patient" in win_text.lower() and "search" in win_text.lower():
                        log_print(f"Found Patient Search window (method 2): '{win_text}'")
                        return app, patient_search
                except:
                    pass
        except Exception as e:
            pass  # Continue trying
        
        # Method 3: Search all child windows by class first
        try:
            child_windows = main_window.children(control_type="Window")
            for child in child_windows:
                try:
                    child_text = child.window_text()
                    child_class = child.element_info.class_name
                    if ("patient" in child_text.lower() and "search" in child_text.lower()) and "ThunderRT6FormDC" in child_class:
                        log_print(f"Found Patient Search window (method 3): '{child_text}'")
                        return app, child
                except:
                    continue
        except Exception as e:
            pass  # Continue trying
        
        # Method 4: Try without class name requirement (more lenient)
        try:
            child_windows = main_window.children(control_type="Window")
            for child in child_windows:
                try:
                    child_text = child.window_text()
                    if "patient" in child_text.lower() and "search" in child_text.lower():
                        log_print(f"Found Patient Search window (method 4, lenient): '{child_text}'")
                        return app, child
                except:
                    continue
        except Exception as e:
            pass  # Continue trying
        
        time.sleep(0.5)

    log_print(f"Patient Search window not found after waiting {max_wait} seconds")
    log_print("Attempted multiple detection methods but window was not found")
    
    # Debug: List all child windows to help diagnose
    try:
        log_print("Debug: Listing all child windows...")
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


def click_dob_radio_button(is_first=True):
    """
    Click on the DOB radio button in the Patient Search window.

    DOB radio button properties:
        - Name: "DOB"
        - ControlType: RadioButton
        - ClassName: "ThunderRT6OptionButton"
        - AutomationId: "12"

    Args:
        is_first: If True, search from main window; if False, search from desktop first, then fallback to main window

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


def click_last_name_radio_button(is_first=True):
    """
    Click on the Last Name radio button in the Patient Search window.

    Last Name radio button properties:
        - Name: "Last Name"
        - ControlType: RadioButton
        - ClassName: "ThunderRT6OptionButton"
        - AutomationId: "19"

    Args:
        is_first: If True, search from main window; if False, search from desktop first, then fallback to main window

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


def type_last_name_in_textbox(last_name, is_first=True):
    """
    Type last name into the textbox in Patient Search window.

    Last Name textbox properties:
        - ControlType: Edit
        - ClassName: "ThunderRT6TextBox"
        - AutomationId: "14"

    Args:
        last_name: The last name to type
        is_first: If True, search from main window; if False, search from desktop first, then fallback to main window

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


def type_dob_in_textbox(dob_string, is_first=True):
    """
    Type DOB into the date textbox in Patient Search window.

    The DOB should be in MMddyyyy format (e.g., "01011980" for January 1, 1980).
    Characters are typed one by one for reliability with this OLE control.

    DOB textbox properties:
        - ControlType: Pane
        - ClassName: "AfxOleControl42"

    Args:
        dob_string: DOB in MMddyyyy format (e.g., "01011980")
        is_first: If True, search from main window; if False, search from desktop first, then fallback to main window

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


def click_search_button(is_first=True):
    """
    Click the search button next to the DOB textbox in Patient Search window.

    Search button properties:
        - Name: "" (empty)
        - ControlType: Button
        - ClassName: "ThunderRT6CommandButton"
        - AutomationId: "13"

    Args:
        is_first: If True, search from main window; if False, search from desktop first, then fallback to main window

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


def search_patient_by_dob_and_last_name(window, dob_string, last_name, is_first):
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
    if is_first:
        # Step 1: Open Patient Search
        if not open_patient_search(window):
            log_print("Failed to open Patient Search")
            return False
        log_print("Patient Search opened successfully!")
    else:
        # Step 1: click Patient Search button
        if not click_patient_search_button():
            log_print("Failed to open Patient Search button")
            return False
        log_print("Patient Search clicked successfully!")
        
        # Wait for Patient Search window to appear
        log_print("Waiting for Patient Search window to appear...")
        time.sleep(3)  # Wait longer for window to start appearing after button click
        
        # Get fresh main window connection to ensure we have latest state
        app, main_window = get_eivf_main_window()
        if main_window:
            log_print("Got fresh main window connection")
        
        # Try to find the window with longer wait time
        if not find_patient_search_window(max_wait=15):
            log_print("ERROR: Patient Search window did not appear after clicking button")
            # Try one more time with fresh connection and longer wait
            log_print("Retrying with fresh connection...")
            time.sleep(2)
            app, main_window = get_eivf_main_window()
            if main_window:
                log_print("Got fresh main window connection (retry)")
            if not find_patient_search_window(max_wait=10):
                log_print("ERROR: Patient Search window still not found after retry")
                return False
        log_print("Patient Search window detected!")

    # Step 2: Click DOB radio button
    if not click_dob_radio_button(is_first=is_first):
        log_print("Failed to click DOB radio button")
        return False
    log_print("DOB radio button clicked!")

    # Step 3: Type DOB
    if not type_dob_in_textbox(dob_string, is_first=is_first):
        log_print("Failed to type DOB")
        return False
    log_print(f"DOB '{dob_string}' entered successfully!")

    # Step 4: Click Search button (first search by DOB)
    if not click_search_button(is_first=is_first):
        log_print("Failed to click search button")
        return False
    log_print("Search button clicked (DOB search)!")
    time.sleep(1)  # Wait for results

    # Step 5: Click Last Name radio button
    if not click_last_name_radio_button(is_first=is_first):
        log_print("Failed to click Last Name radio button")
        return False
    log_print("Last Name radio button clicked!")

    # Step 6: Type Last Name
    if not type_last_name_in_textbox(last_name, is_first=is_first):
        log_print("Failed to type Last Name")
        return False
    log_print(f"Last Name '{last_name}' entered successfully!")

    log_print("=== Patient DOB + Last Name search completed successfully ===")
    return True


def click_select_button(is_first=True):
    """
    Click the 'Select' button in the Patient Search window.

    Args:
        is_first: If True, search from main window; if False, search from desktop first, then fallback to main window

    Returns:
        True if successful, False otherwise
    """
    log_print("Clicking Select button...")

    try:
        # Get the Patient Search window
        app, search_window = get_patient_search_window()

        if not search_window:
            log_print("Could not find Patient Search window")
            return False

        # Try to find the Select button by title
        select_button = search_window.child_window(
            title="Select",
            control_type="Button"
        )

        if select_button.exists(timeout=3):
            select_button.click_input()
            log_print("Select button clicked successfully")
            time.sleep(1)
            return True

        # Try by class name if title didn't work
        buttons = search_window.children(control_type="Button")
        for btn in buttons:
            try:
                btn_text = btn.window_text()
                if "select" in btn_text.lower():
                    btn.click_input()
                    log_print(f"Select button clicked (found as '{btn_text}')")
                    time.sleep(1)
                    return True
            except:
                continue

        log_print("Select button not found")
        return False

    except Exception as e:
        log_print(f"Error clicking Select button: {str(e)}")
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



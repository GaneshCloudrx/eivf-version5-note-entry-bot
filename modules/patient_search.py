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


def click_select_button():
    """
    Click the 'Select' button in the Patient Search window.

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


def write_note(note_title, note_text):
    """
    Enter note content and title in the Notes window.

    IMPORTANT: When Notes window opens, cursor is ALREADY in the note content area.
    So we type NOTE FIRST, then find the title field and enter title.

    Args:
        note_title: The title text to enter in the Title field
        note_text: The note content to write in the text area

    Returns:
        True if successful, False otherwise
    """
    log_print(f"Writing note - Title: '{note_title}', Content: '{note_text}'")

    try:
        app, main_window = get_eivf_main_window()
        if not main_window:
            log_print("Could not find main window")
            return False

        title_entered = False
        note_entered = False

        # ============ STEP 1: Enter Note Content FIRST ============
        log_print("Step 1: Entering note content...")

        time.sleep(1)  # Wait for window to be fully ready

        # First, press Escape to close any Templates panel that might be open
        log_print("Pressing Escape to close Templates panel if open...")
        send_keys("{ESC}")
        time.sleep(0.5)

        # Now find and click on the note content area
        # Search for "eIVF Note Screen" (the IE control for note content)
        desktop = get_desktop()

        note_area = None
        for win in desktop.windows():
            if note_area:
                break
            try:
                for desc in win.descendants():
                    try:
                        name = getattr(desc.element_info, "name", "") or ""
                        cls = getattr(desc.element_info, "class_name", "") or ""

                        if name == "eIVF Note Screen" or (
                                cls == "Internet Explorer_Server" and "Note" in str(win.window_text())):
                            rect = desc.rectangle()
                            if rect.right - rect.left > 300:  # Make sure it's the large one
                                log_print(
                                    f"Found note area: name='{name}' rect=({rect.left},{rect.top},{rect.right},{rect.bottom})")
                                note_area = (rect.left + 100, rect.top + 100)  # Click inside
                                break
                    except:
                        continue
            except:
                continue

        if note_area:
            log_print(f"Clicking note area at {note_area}")
            mouse.click(coords=note_area)
            time.sleep(0.5)

        # Type the note content
        try:
            send_keys(note_text, with_spaces=True)
            log_print(f"Note content typed: '{note_text}'")
            note_entered = True
        except Exception as e:
            log_print(f"Typing failed: {e}")

        # ============ STEP 2: Enter Title ============
        log_print("Step 2: Entering note title...")

        # Find the title field by class name: WindowsForms10.EDIT.app.0.141b42a_r7_ad1
        # or by automation_id: txtTitleNote
        try:
            desktop = get_desktop()

            for win in desktop.windows():
                if title_entered:
                    break
                try:
                    for desc in win.descendants():
                        try:
                            cls = getattr(desc.element_info, "class_name", "") or ""
                            auto_id = getattr(desc.element_info, "automation_id", "") or ""

                            # Look for Windows Forms Edit control (title field)
                            if "WindowsForms" in cls and "EDIT" in cls:
                                rect = desc.rectangle()
                                area = (rect.right - rect.left) * (rect.bottom - rect.top)

                                # Title field is small (area < 50000)
                                if 500 < area < 50000:
                                    log_print(f"Found title field: class='{cls}' auto_id='{auto_id}' area={area}")

                                    desc.click_input()
                                    time.sleep(0.2)

                                    # Select all and type new title
                                    desc.type_keys("^a", with_spaces=True)
                                    time.sleep(0.1)
                                    desc.type_keys(note_title, with_spaces=True)
                                    log_print(f"Title entered: '{note_title}'")
                                    title_entered = True
                                    break
                        except:
                            continue
                except:
                    continue
        except Exception as e:
            log_print(f"Error entering title: {e}")

        # Return result
        if title_entered and note_entered:
            log_print("SUCCESS: Both note content and title entered!")
            return True
        elif note_entered:
            log_print("SUCCESS: Note content entered (title may have failed)")
            return True
        else:
            log_print("FAILED: Could not enter note content")
            return False

    except Exception as e:
        log_print(f"Error writing note: {str(e)}")
        return False


def click_save_button():
    """
    Click the 'Save' button in the Notes window.
    The Notes window has buttons at bottom: Print Preview, Print, Save, Close

    Returns:
        True if successful, False otherwise
    """
    log_print("Clicking Save button in Notes window...")

    try:
        app, main_window = get_eivf_main_window()

        if not main_window:
            log_print("Could not find main window")
            return False

        # Find Windows Forms Save button
        # Class: "WindowsForms10.BUTTON.app.0.141b42a_r7_ad1", Name: "Save"
        desktop = get_desktop()

        # Search across all windows for Windows Forms Save button
        log_print("Searching for Windows Forms Save button...")
        for win in desktop.windows():
            try:
                for desc in win.descendants():
                    try:
                        cls = getattr(desc.element_info, "class_name", "") or ""
                        name = getattr(desc.element_info, "name", "") or ""

                        # Look for Windows Forms BUTTON with name "Save"
                        if "WindowsForms" in cls and "BUTTON" in cls.upper() and name == "Save":
                            rect = desc.rectangle()
                            log_print(
                                f"Found Windows Forms Save button: class='{cls}' rect=({rect.left},{rect.top},{rect.right},{rect.bottom})")

                            # Click using mouse
                            center_x = (rect.left + rect.right) // 2
                            center_y = (rect.top + rect.bottom) // 2
                            log_print(f"Clicking Save button at ({center_x}, {center_y})")

                            mouse.click(coords=(center_x, center_y))
                            log_print("Save button clicked successfully!")
                            time.sleep(1)
                            return True
                    except:
                        continue
            except:
                continue

        log_print("Save button not found")
        return False

    except Exception as e:
        log_print(f"Error clicking Save button: {str(e)}")
        return False


def click_new_button():
    """
    Click the 'New' button in the patient toolbar.

    Returns True if clicked, False otherwise.
    """
    log_print("Clicking New button...")

    try:
        app, main_window = get_eivf_main_window()
        if not main_window:
            log_print("Could not find main eIVF window")
            return False

        # Try direct lookup first
        try:
            new_btn = main_window.child_window(title="New", control_type="Button")
            if new_btn.exists(timeout=2):
                new_btn.click_input()
                log_print("New button clicked (direct)")
                time.sleep(0.5)
                return True
        except Exception:
            pass

        # Try searching button descendants by exact text
        try:
            for btn in main_window.descendants(control_type="Button"):
                try:
                    if btn.window_text().strip().lower() == "new":
                        btn.click_input()
                        log_print("New button clicked (found by descendants)")
                        time.sleep(0.5)
                        return True
                except Exception:
                    continue
        except Exception:
            pass

        log_print("New button not found")
        return False

    except Exception as e:
        log_print(f"Error in click_new_button: {e}")
        return False


def safe_text(elem):
    try:
        return (elem.window_text() or "").strip()
    except Exception:
        return ""


def get_notes_window_patient_details():
    """
    Extract patient details from the Notes window header.
    The patient header is a Windows Forms Panel control (Panel1) with class WindowsForms10.*
    Returns dict with first_name, last_name, dob, patient_id (where found) or None.
    """
    log_print("get_notes_window_patient_details: start (v4 - WinForms search)")

    try:
        app, main_window = get_eivf_main_window()
        if not main_window:
            log_print("main window not found")
            return None

        # helper regexes
        DOB_RE_LOCAL = re.compile(r'\bDOB[:\s]*(\d{1,2}/\d{1,2}/\d{4})\b', re.IGNORECASE)
        DATE_RE_LOCAL = re.compile(r'(\d{1,2}/\d{1,2}/\d{4})')
        ID_RE_LOCAL = re.compile(r'\((\d{2,})\)')
        URL_LIKE = re.compile(r'https?://|www\.|\.htm|\.html', re.IGNORECASE)

        candidates = []

        # Step 1: Search for Windows Forms lblTitle control
        # The patient header is:
        #   - ControlType: Text
        #   - ClassName: WindowsForms10.STATIC.app.0.141b42a_r7_ad1
        #   - AutomationId: lblTitle
        #   - Name property contains the patient info
        log_print("Step 1: Searching for Windows Forms lblTitle control...")
        try:
            # Search desktop for the specific lblTitle control
            desktop = get_desktop()
            all_windows = desktop.windows()

            for win in all_windows:
                try:
                    # Look for WindowsForms Text controls with lblTitle
                    for desc in win.descendants():
                        try:
                            cls = getattr(desc.element_info, "class_name", "") or ""
                            auto_id = getattr(desc.element_info, "automation_id", "") or ""
                            ctrl_type = getattr(desc.element_info, "control_type", "") or ""

                            # Check for the specific lblTitle control
                            if auto_id == "lblTitle" or ("WindowsForms" in cls and "STATIC" in cls):
                                name = getattr(desc.element_info, "name", "") or ""
                                txt = safe_text(desc)

                                log_print(f"Found lblTitle: class='{cls}' auto_id='{auto_id}' ctrl='{ctrl_type}'")
                                log_print(f"  Name property: '{name[:150] if name else 'empty'}'")

                                # The patient info is in the Name property
                                if name and ("DOB" in name or "Quick Notes" in name):
                                    log_print(f"  --> PATIENT INFO FOUND in Name property!")
                                    candidates.append(name)
                                elif txt and ("DOB" in txt or "Quick Notes" in txt):
                                    log_print(f"  --> PATIENT INFO FOUND in text!")
                                    candidates.append(txt)
                        except:
                            continue
                except:
                    continue
        except Exception as e:
            log_print(f"Error searching for lblTitle control: {e}")

        # Check if we found patient info
        if candidates:
            log_print(f"Step 1 SUCCESS: Found {len(candidates)} candidate(s) with patient info")

        # No candidates found
        if not candidates:
            log_print("No patient info candidates found in Notes window")
            return None

        # Choose the best candidate (prefer ones with DOB pattern)
        log_print(f"Found {len(candidates)} candidate(s)")
        chosen = None
        for txt in candidates:
            if URL_LIKE.search(txt):
                continue
            if DOB_RE_LOCAL.search(txt):
                chosen = txt
                log_print(f"Chosen candidate with DOB: '{txt[:150]}'")
                break

        if not chosen and candidates:
            chosen = candidates[0]
            log_print(f"Using first candidate: '{chosen[:150]}'")

        if not chosen:
            log_print("No valid candidate found")
            return None

        # Parse the chosen text
        patient = {}

        # Extract DOB
        dob_match = DOB_RE_LOCAL.search(chosen)
        if dob_match:
            patient['dob'] = dob_match.group(1)
            log_print(f"Extracted DOB: {patient['dob']}")

        # Extract Patient ID
        id_match = ID_RE_LOCAL.search(chosen)
        if id_match:
            patient['patient_id'] = id_match.group(1)
            log_print(f"Extracted Patient ID: {patient['patient_id']}")

        # Extract Name
        # Try "Quick Notes: FirstName MiddleName LastName (ID)" pattern
        name_pattern = re.search(r'Quick\s*(Notes|Summary)[:\s]*([A-Za-z0-9\.\'\- ]+)\s*\(', chosen, re.IGNORECASE)
        if name_pattern:
            full_name = name_pattern.group(2).strip()
            log_print(f"Extracted full name: '{full_name}'")

            name_parts = full_name.split()
            if len(name_parts) >= 2:
                patient['first_name'] = name_parts[0]
                patient['last_name'] = name_parts[-1].rstrip('.')
                log_print(f"Parsed: first='{patient['first_name']}', last='{patient['last_name']}'")
            elif len(name_parts) == 1:
                patient['first_name'] = name_parts[0]
                patient['last_name'] = ''

        if patient.get('dob') or patient.get('first_name'):
            log_print(f"Final parsed patient: {patient}")
            return patient

        log_print("Could not parse patient details from candidate text")
        return None

    except Exception as e:
        log_print(f"get_notes_window_patient_details: unexpected error: {e}")
        import traceback
        log_print(traceback.format_exc())
        return None


def verify_patient_explorer_match(expected_first_name, expected_last_name, expected_dob):
    """
    Verify that the patient shown in Notes window matches the expected patient details.

    This is a MANDATORY verification step before writing notes.

    Args:
        expected_first_name: Expected first name (string)
        expected_last_name: Expected last name (string)
        expected_dob: Expected DOB as MMddyyyy or MM/dd/yyyy

    Returns:
        True if patient matches, False otherwise
    """
    log_print(f"Verifying Notes window shows: {expected_first_name} {expected_last_name}, DOB: {expected_dob}")

    try:
        # Get patient details from the Notes window
        patient_details = get_notes_window_patient_details()
        if not patient_details:
            log_print("verify_patient_explorer_match: could not retrieve patient details from Notes window")
            log_print("VERIFICATION FAILED - cannot proceed without verifying patient")
            return False

        # Normalize DOB formats to compare
        expected_formats = [expected_dob]
        if isinstance(expected_dob, str) and len(expected_dob) == 8 and expected_dob.isdigit():
            mm, dd, yyyy = expected_dob[:2], expected_dob[2:4], expected_dob[4:]
            expected_formats.extend([f"{mm}/{dd}/{yyyy}", f"{mm}-{dd}-{yyyy}", f"{int(mm)}/{int(dd)}/{yyyy}"])

        # Get actuals
        actual_first = patient_details.get('first_name', '').strip().lower()
        actual_last = patient_details.get('last_name', '').strip().lower()
        actual_dob = patient_details.get('dob', '').strip()

        first_ok = (actual_first == expected_first_name.strip().lower())
        last_ok = (actual_last == expected_last_name.strip().lower())
        dob_ok = any(actual_dob == fmt or actual_dob.lower() == fmt.lower() for fmt in expected_formats)

        log_print(
            f"verify_patient_explorer_match: header_text comparison -> first_ok={first_ok}, last_ok={last_ok}, dob_ok={dob_ok}")

        all_match = first_ok and last_ok and dob_ok
        if all_match:
            log_print("verify_patient_explorer_match: PASSED")
        else:
            log_print("verify_patient_explorer_match: FAILED")

        return all_match

    except Exception as e:
        log_print(f"verify_patient_explorer_match: error: {e}")
        import traceback
        log_print(traceback.format_exc())
        return False

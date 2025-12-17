from pywinauto import Desktop, mouse
from pywinauto.keyboard import send_keys
import time
import re

from modules.patient_search import get_eivf_main_window
from modules.utils import log_print


# Reusable Desktop instance for UIA backend
def get_desktop():
    """Get Desktop instance with UIA backend."""
    return Desktop(backend="uia")

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

"""
Note addition module - handles adding notes to patient records in eIVF
"""
import time
import re
import pyperclip
from pywinauto import Application, Desktop, mouse
from pywinauto.keyboard import send_keys

import modules.helper as helper
import modules.patient_search as patient_search
from config import UI_ACTION_TIMEOUT


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
    helper.log_print(f"Writing note - Title: '{note_title}', Content: '{note_text}'")
    note_text = re.sub(r"<br>|</br>|<br/>|</n>", "\n", note_text).strip()

    try:
        app, main_window = patient_search.get_eivf_main_window()
        if not main_window:
            helper.log_print("Could not find main window")
            return False

        title_entered = False
        note_entered = False

        # ============ STEP 1: Enter Note Content FIRST ============
        helper.log_print("Step 1: Entering note content...")

        time.sleep(1)  # Wait for window to be fully ready


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
                                helper.log_print(
                                    f"Found note area: name='{name}' rect=({rect.left},{rect.top},{rect.right},{rect.bottom})")
                                note_area = (rect.left + 100, rect.top + 100)  # Click inside
                                break
                    except:
                        continue
            except:
                continue

        if note_area:
            helper.log_print(f"Clicking note area at {note_area}")
            helper.run_with_timeout(lambda a=note_area: mouse.click(coords=a), timeout_seconds=UI_ACTION_TIMEOUT)
            time.sleep(0.5)

        # Paste the note content using clipboard (preserves newlines)
        try:
            pyperclip.copy(note_text)
            helper.log_print("Note content copied to clipboard")
            helper.run_with_timeout(lambda: send_keys("^v"), timeout_seconds=UI_ACTION_TIMEOUT)  # Ctrl+V to paste
            time.sleep(0.3)
            helper.log_print(f"Note content pasted: '{note_text}'")
            note_entered = True
        except Exception as e:
            helper.log_print(f"Pasting failed: {e}")

        # ============ STEP 2: Enter Title ============
        helper.log_print("Step 2: Entering note title...")

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
                                    helper.log_print(f"Found title field: class='{cls}' auto_id='{auto_id}' area={area}")

                                    desc.click_input()
                                    time.sleep(0.2)

                                    # Select all and type new title
                                    desc.type_keys("^a", with_spaces=True)
                                    time.sleep(0.1)
                                    desc.type_keys(note_title, with_spaces=True)
                                    helper.log_print(f"Title entered: '{note_title}'")
                                    title_entered = True
                                    break
                        except:
                            continue
                except:
                    continue
        except Exception as e:
            helper.log_print(f"Error entering title: {e}")

        # Return result
        if title_entered and note_entered:
            helper.log_print("SUCCESS: Both note content and title entered!")
            return True
        elif note_entered:
            helper.log_print("SUCCESS: Note content entered (title may have failed)")
            return True
        else:
            helper.log_print("FAILED: Could not enter note content")
            return False

    except Exception as e:
        helper.log_print(f"Error writing note: {str(e)}")
        return False


def click_save_button():
    """
    Click the 'Save' button in the Notes window using win32 backend.
    The Notes window has buttons at bottom: Print Preview, Print, Save, Close

    Returns:
        True if successful, False otherwise
    """
    helper.log_print("Clicking Save button in Notes window (win32 approach)...")

    try:
        # Find the Notes window from Desktop and get its process ID
        desktop = Desktop(backend="win32")
        
        notes_pid = None
        for win in desktop.windows():
            try:
                title = win.window_text()
                if "Notes" in title and "Quick Summary" in title:
                    notes_pid = win.process_id()
                    helper.log_print(f"Found Notes window: '{title}' with PID: {notes_pid}")
                    break
            except:
                pass
        
        if not notes_pid:
            helper.log_print("Notes window not found")
            return False
        
        # Connect to the Notes application using win32 backend
        app = Application(backend="win32").connect(process=notes_pid)
        
        # Get the Notes window
        notes_window = app.window(title_re=".*Notes.*Quick Summary.*")
        notes_window.wait("visible", timeout=10)
        helper.log_print("Connected to Notes window")
        
        # Find the Save button using class_name regex and title
        # From inspect.exe: ClassName: "WindowsForms10.BUTTON...", Name: "Save", AutomationId: "btnSave2"
        try:
            save_button = notes_window.child_window(
                class_name_re=".*WindowsForms10\\.BUTTON.*",
                title="Save"
            )
            save_button.wait("visible", timeout=5)
            helper.log_print(f"Found Save button: {save_button.window_text()}")
            
            # Focus the window first
            notes_window.set_focus()
            time.sleep(0.3)
            
            # Focus the button and click
            save_button.set_focus()
            time.sleep(0.2)
            save_button.click_input()
            helper.log_print("Save button clicked successfully!")
            time.sleep(0.5)
            
            # Take screenshot after save
            helper.take_screenshot(prefix="note_saved")
            
            time.sleep(0.5)
            return True
            
        except Exception as e:
            helper.log_print(f"Primary method failed: {e}")
            
            # Fallback: try with auto_id
            helper.log_print("Trying fallback with auto_id='btnSave2'...")
            try:
                save_button = notes_window.child_window(auto_id="btnSave2")
                save_button.wait("visible", timeout=5)
                helper.log_print(f"Found Save button via auto_id: {save_button.window_text()}")
                
                # Focus the window first
                notes_window.set_focus()
                time.sleep(0.3)
                
                # Focus the button and click
                save_button.set_focus()
                time.sleep(0.2)
                save_button.click_input()
                helper.log_print("Save button clicked successfully!")
                time.sleep(0.5)
                
                # Take screenshot after save
                helper.take_screenshot(prefix="note_saved")
                
                time.sleep(0.5)
                return True
            except Exception as e2:
                helper.log_print(f"Fallback also failed: {e2}")
                return False

    except Exception as e:
        helper.log_print(f"Error clicking Save button: {str(e)}")
        return False


def click_new_button():
    """
    Click the 'New' button in the patient toolbar.
    Only clicks New button if checkboxes "Results" (auto_id=31) and "Schedule" (auto_id=32) exist.
    If checkboxes don't exist, returns False to skip to next note.

    Returns True if clicked, False otherwise.
    """
    helper.log_print("Checking for required checkboxes before clicking New button...")

    try:
        app, main_window = patient_search.get_eivf_main_window()
        if not main_window:
            helper.log_print("Could not find main eIVF window")
            return False

        # Click Results checkbox (control_id=31) then All checkbox (control_id=35)
        helper.log_print("Clicking Results checkbox (control_id=31)...")
        
        try:
            # Use win32 backend for VB6 controls
            from pywinauto import Application
            app_win32 = Application(backend="win32").connect(class_name="ThunderRT6MDIForm", title="eIVF")
            eivf_window = app_win32.window(class_name="ThunderRT6MDIForm", title="eIVF")
            
            #Find and click notes checkbox with dynamic wait
            notes_checkbox = eivf_window.child_window(
                class_name="ThunderRT6CheckBox",
                control_id=37
            )
            notes_checkbox.wait("exists enabled", timeout=30)
            notes_checkbox.set_focus()
            notes_checkbox.click_input()
            helper.log_print("✔ Notes checkbox clicked")
            time.sleep(1)
            
            # Find and click All checkbox
            helper.log_print("Clicking All checkbox (control_id=35)...")
            # Reconnect to window after clicking Results to ensure fresh reference
            eivf_window = app_win32.window(class_name="ThunderRT6MDIForm", title="eIVF")
            all_checkbox = eivf_window.child_window(
                class_name="ThunderRT6CheckBox",
                control_id=35
            )
            all_checkbox.wait("exists enabled", timeout=10)
            all_checkbox.set_focus()
            all_checkbox.click_input()
            helper.log_print("✔ All checkbox clicked")
            time.sleep(1)

            
                # Assume it's checked since we clicked it
            
        except Exception as e:
            helper.log_print(f"❌ Error clicking checkboxes: {e}")
            helper.log_print("Required checkboxes missing - skipping to next note")
            return False

        # Checkboxes clicked, proceed to click New button
        helper.log_print("Checkboxes ready. Clicking New button...")

        # Try direct lookup first
        try:
            new_btn = main_window.child_window(title="New", control_type="Button")
            if new_btn.exists(timeout=2):
                new_btn.invoke()
                helper.log_print("New button clicked (direct)")
                time.sleep(1)  # Brief wait, dynamic wait happens in verification
                return True
        except Exception:
            pass

        # Try searching button descendants by exact text
        try:
            for btn in main_window.descendants(control_type="Button"):
                try:
                    if btn.window_text().strip().lower() == "new":
                        btn.click_input()
                        helper.log_print("New button clicked (found by descendants)")
                        time.sleep(0.5)
                        return True
                except Exception:
                    continue
        except Exception:
            pass

        helper.log_print("New button not found")
        return False

    except Exception as e:
        helper.log_print(f"Error in click_new_button: {e}")
        return False


def get_notes_window_patient_details():
    """
    Extract patient details from the Notes window header using win32 backend.
    Uses simpler approach: find Notes window, get lblTitle label, extract text.
    Returns dict with first_name, last_name, dob, patient_id, phone_number (where found) or None.
    """
    helper.log_print("get_notes_window_patient_details: start (v5 - win32 approach)")

    try:
        # Step 1: Find Notes window from Desktop and get its PID
        desktop = Desktop(backend="win32")
        
        notes_pid = None
        for win in desktop.windows():
            try:
                title = win.window_text()
                if "Notes" in title and "Quick Summary" in title:
                    notes_pid = win.process_id()
                    helper.log_print(f"Found Notes window: {title}, PID: {notes_pid}")
                    break
            except:
                pass
        
        if not notes_pid:
            helper.log_print("Notes window not found")
            return None
        
        # Step 2: Connect to the Notes application using its PID
        app = Application(backend="win32").connect(process=notes_pid)
        notes_window = app.window(title_re=".*Notes.*Quick Summary.*")
        
        # Step 3: Find lblTitle label - the one that contains "Quick Notes:"
        lbl_title = notes_window.child_window(class_name_re=".*WindowsForms10\\.STATIC.*", title_re=".*Quick Notes.*")
        patient_info = lbl_title.window_text()
        helper.log_print(f"Patient Info: {patient_info}")
        
        if not patient_info:
            helper.log_print("Could not extract patient info from lblTitle")
            return None
        
        # Step 4: Parse the patient info text
        # Helper regexes
        DOB_RE_LOCAL = re.compile(r'\bDOB[:\s]*(\d{1,2}/\d{1,2}/\d{4})\b', re.IGNORECASE)
        ID_RE_LOCAL = re.compile(r'\((\d{2,})\)')
        
        patient = {}
        
        # Extract DOB
        dob_match = DOB_RE_LOCAL.search(patient_info)
        if dob_match:
            patient['dob'] = dob_match.group(1)
            helper.log_print(f"Extracted DOB: {patient['dob']}")
        
        # Extract Patient ID
        id_match = ID_RE_LOCAL.search(patient_info)
        if id_match:
            patient['patient_id'] = id_match.group(1)
            helper.log_print(f"Extracted Patient ID: {patient['patient_id']}")
        
        # Extract Phone Number (patterns like "(000) 000-0000" or "M:(000) 000-0000")
        phone_patterns = [
            re.compile(r'M:\s*\(?(\d{3})\)?\s*-?\s*(\d{3})\s*-?\s*(\d{4})', re.IGNORECASE),
            re.compile(r'\((\d{3})\)\s*-?\s*(\d{3})\s*-?\s*(\d{4})', re.IGNORECASE),
        ]
        for phone_pattern in phone_patterns:
            phone_match = phone_pattern.search(patient_info)
            if phone_match:
                phone_number = f"({phone_match.group(1)}) {phone_match.group(2)}-{phone_match.group(3)}"
                patient['phone_number'] = phone_number
                helper.log_print(f"Extracted Phone Number: {patient['phone_number']}")
                break
        
        # Extract Name - "Quick Notes: FirstName LastName (ID)" pattern
        name_pattern = re.search(r'Quick\s*(Notes|Summary)[:\s]*([A-Za-z0-9\.\'\- ]+)\s*\(', patient_info, re.IGNORECASE)
        if name_pattern:
            full_name = name_pattern.group(2).strip()
            helper.log_print(f"Extracted full name: '{full_name}'")
            
            name_parts = full_name.split()
            if len(name_parts) >= 2:
                patient['first_name'] = name_parts[0]
                patient['last_name'] = name_parts[-1].rstrip('.')
                helper.log_print(f"Parsed: first='{patient['first_name']}', last='{patient['last_name']}'")
            elif len(name_parts) == 1:
                patient['first_name'] = name_parts[0]
                patient['last_name'] = ''
        
        if patient.get('dob') or patient.get('first_name'):
            helper.log_print(f"Final parsed patient: {patient}")
            return patient
        
        helper.log_print("Could not parse patient details from text")
        return None

    except Exception as e:
        helper.log_print(f"get_notes_window_patient_details: unexpected error: {e}")
        import traceback
        helper.log_print(traceback.format_exc())
        return None


def close_notes_window():
    """
    Close the Notes window by finding and clicking the Close button.
    Uses the same approach as click_save_button - searches for Windows Forms Close button.
    
    Returns:
        True if successful, False otherwise
    """
    helper.log_print("Attempting to close Notes window...")
    
    try:
        app, main_window = patient_search.get_eivf_main_window()
        if not main_window:
            helper.log_print("Could not find main window to close Notes")
            return False
        
        # Find Windows Forms Close button (same approach as Save button)
        # Class: "WindowsForms10.BUTTON.app.0.141b42a_r7_ad1", Name: "Close"
        desktop = get_desktop()
        
        helper.log_print("Searching for Windows Forms Close button...")
        for win in desktop.windows():
            try:
                win_title = win.window_text()
                # Check if this is the Notes window
                if "Notes" in win_title and "Quick Summary" in win_title:
                    helper.log_print(f"Found Notes window: '{win_title}'")
                    
                    # Focus the Notes window first
                    win.set_focus()
                    time.sleep(0.5)
                    helper.log_print("Notes window focused")
                    
                    for desc in win.descendants():
                        try:
                            cls = getattr(desc.element_info, "class_name", "") or ""
                            name = getattr(desc.element_info, "name", "") or ""
                            
                            # Look for Windows Forms BUTTON with name "Close"
                            if "WindowsForms" in cls and "BUTTON" in cls.upper() and name == "Close":
                                rect = desc.rectangle()
                                helper.log_print(
                                    f"Found Windows Forms Close button: class='{cls}' rect=({rect.left},{rect.top},{rect.right},{rect.bottom})")
                                
                                # Click using mouse (with timeout to prevent hang)
                                center_x = (rect.left + rect.right) // 2
                                center_y = (rect.top + rect.bottom) // 2
                                helper.log_print(f"Clicking Close button at ({center_x}, {center_y})")
                                
                                helper.run_with_timeout(
                                    lambda cx=center_x, cy=center_y: mouse.click(coords=(cx, cy)),
                                    timeout_seconds=UI_ACTION_TIMEOUT
                                )
                                helper.log_print("Close button clicked successfully!")
                                time.sleep(1)
                                return True
                        except:
                            continue
            except:
                continue
        
        helper.log_print("Close button not found - trying Escape key as fallback...")
        # Fallback: Try Escape key (with timeout to prevent hang)
        try:
            helper.run_with_timeout(
                lambda: (main_window.set_focus(), time.sleep(0.3), send_keys("{ESC}", with_spaces=True)),
                timeout_seconds=UI_ACTION_TIMEOUT
            )
            time.sleep(0.5)
            helper.log_print("Notes window closed using Escape (fallback)")
            return True
        except Exception as e:
            helper.log_print(f"Escape key also failed: {e}")
        
        helper.log_print("Could not close Notes window")
        return False
        
    except Exception as e:
        helper.log_print(f"Error closing Notes window: {e}")
        return False


def verify_patient_explorer_match(expected_dob, expected_last_name=None, expected_first_name=None):
    """
    Verify that the patient shown in Notes window matches the expected patient DOB, first name, and last name.

    This is a MANDATORY verification step before writing notes.
    Checks if the expected DOB string is contained in the patient info text.
    If last name is provided, also checks if the last name is present (for DOB-based searches).

    Args:
        expected_dob: Expected date of birth (string, format: MMDDYYYY or MM/DD/YYYY)
        expected_last_name: Expected last name (optional, for enhanced verification in DOB searches)

    Returns:
        True if DOB (and last name if provided) is found in patient info, False otherwise
    """
    if expected_last_name:
        helper.log_print(f"Verifying Notes window contains DOB: {expected_dob} and Last Name: {expected_last_name}")
    else:
        helper.log_print(f"Verifying Notes window contains DOB: {expected_dob}")

    try:
        # Step 1: Format DOB - convert MMDDYYYY to MM/DD/YYYY if needed
        formatted_dob = expected_dob
        if len(expected_dob) == 8 and expected_dob.isdigit():
            # Format: MMDDYYYY -> MM/DD/YYYY
            formatted_dob = f"{expected_dob[0:2]}/{expected_dob[2:4]}/{expected_dob[4:8]}"
            helper.log_print(f"Formatted DOB from '{expected_dob}' to '{formatted_dob}'")
        
        # Step 2: Find Notes window and extract raw patient info text
        # Dynamic wait - check every 1 second for up to 30 seconds
        desktop = Desktop(backend="win32")
        
        notes_pid = None
        max_wait_time = 30  # Maximum wait time in seconds
        check_interval = 1  # Check every 1 second
        elapsed_time = 0
        
        helper.log_print(f"Waiting for Notes window (max {max_wait_time}s)...")
        
        while elapsed_time < max_wait_time:
            for win in desktop.windows():
                try:
                    title = win.window_text()
                    if "Notes" in title and "Quick Summary" in title:
                        notes_pid = win.process_id()
                        helper.log_print(f"Found Notes window after {elapsed_time}s: {title}, PID: {notes_pid}")
                        break
                except:
                    pass
            
            if notes_pid:
                break  # Window found, exit wait loop
            
            time.sleep(check_interval)
            elapsed_time += check_interval
        
        if not notes_pid:
            helper.log_print(f"verify_patient_explorer_match: Notes window not found after {max_wait_time}s")
            helper.log_print("VERIFICATION FAILED - cannot proceed without verifying patient")
            return False
        
        # Step 3: Connect and get patient info text
        app = Application(backend="win32").connect(process=notes_pid)
        notes_window = app.window(title_re=".*Notes.*Quick Summary.*")
        
        # Find lblTitle label containing patient info
        lbl_title = notes_window.child_window(class_name_re=".*WindowsForms10\\.STATIC.*", title_re=".*Quick Notes.*")
        patient_info = lbl_title.window_text()
        helper.log_print(f"Patient Info Text: {patient_info}")
        
        if not patient_info:
            helper.log_print("verify_patient_explorer_match: could not extract patient info")
            helper.log_print("VERIFICATION FAILED - cannot proceed without verifying patient")
            return False
        
        # Step 4: Check DOB
        dob_found = formatted_dob in patient_info
        
        if not dob_found:
            helper.log_print(f"verify_patient_explorer_match: FAILED - DOB '{formatted_dob}' NOT found in patient info")
            # Close Notes window when verification fails
            helper.log_print("Closing Notes window due to verification failure...")
            close_notes_window()
            return False
        
        helper.log_print(f"✓ DOB '{formatted_dob}' found in patient info")
        
        # Step 5: Check first name if provided (for DOB-based searches)
        if expected_first_name:
            import re
            # Take first word from first name (handles compound names like "Maria Elena")
            first_name_to_check = re.split(r'[\s\-()]', expected_first_name)[0].strip().lower()
            first_name_found = first_name_to_check in patient_info.lower()
            
            if not first_name_found:
                helper.log_print(f"verify_patient_explorer_match: FAILED - First Name '{first_name_to_check}' NOT found in patient info")
                # Close Notes window when verification fails
                helper.log_print("Closing Notes window due to verification failure...")
                close_notes_window()
                return False
            
            helper.log_print(f"✓ First Name '{first_name_to_check}' found in patient info")
        
        # Step 6: Check last name if provided (for DOB-based searches)
        if expected_last_name:
            import re
            # Take last word from last name (handles "Sanchez Torres", "Ampie-mendoza", "Brumagin (Hodge)")
            last_name_to_check = re.split(r'[\s\-()]', expected_last_name)[-1].strip().lower()
            last_name_found = last_name_to_check in patient_info.lower()
            
            if not last_name_found:
                helper.log_print(f"verify_patient_explorer_match: FAILED - Last Name '{last_name_to_check}' NOT found in patient info")
                # Close Notes window when verification fails
                helper.log_print("Closing Notes window due to verification failure...")
                close_notes_window()
                return False
            
            helper.log_print(f"✓ Last Name '{last_name_to_check}' found in patient info")
        
        # Final verification message
        verified_items = ["DOB"]
        if expected_first_name:
            verified_items.append("First Name")
        if expected_last_name:
            verified_items.append("Last Name")
        helper.log_print(f"verify_patient_explorer_match: PASSED - {' and '.join(verified_items)} verified")
        
        return True

    except Exception as e:
        helper.log_print(f"verify_patient_explorer_match: error: {e}")
        import traceback
        helper.log_print(traceback.format_exc())
        # Close Notes window on error
        close_notes_window()
        return False


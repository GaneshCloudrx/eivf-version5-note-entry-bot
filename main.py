"""
eIVF Note Entry Bot - Main Orchestrator
24/7 continuous automation for adding patient notes
"""
import time
import traceback
from pywinauto import Application

# Config
from config import APP_PATH, TARGET_TITLE

# Modules with alias imports
import modules.helper as helper
import modules.login as login
import modules.configuation_change as config_change
import modules.patient_search as patient_search
import modules.color_addition as color
import modules.note_addition as notes
import modules.data_reader as data_reader

# API
from modules.data_from_api import data_from_api, update_api
from modules.api_integration import log_error_to_portal
from config import MAX_PATIENT_FAILURES


# Custom exception for triggering application restart
class RestartEivfException(Exception):
    """Raised when eIVF needs to be restarted"""
    pass


def process_single_note(note_data, clinic_data, is_first, search_method='phone'):
    """
    Process a single patient note entry
    
    Args:
        note_data: Dictionary with patient note data
        clinic_data: Dictionary with clinic data
        is_first: Boolean indicating if this is the first note of the clinic
        search_method: String indicating search method ('phone' or 'dob')
    """
    helper.log_print(f"\n{'='*60}")
    helper.log_print(f"Processing: {note_data['patient_first_name']} {note_data['patient_last_name']}")
    helper.log_print(f"Phone: {note_data['patient_phone']} | Clinic: {note_data['clinic_name']}")
    helper.log_print(f"Search Method: {search_method.upper()}")
    helper.log_print(f"{'='*60}")
    
    first_name = note_data['patient_first_name']
    last_name = note_data['patient_last_name']
    phone = note_data['patient_phone']
    dob = note_data['patient_dob']
    
    # Validate required fields
    if not first_name:
        helper.log_print("ERROR: Missing patient first name")
        return False
    
    if search_method == 'phone' and not phone:
        helper.log_print("ERROR: Missing patient phone for phone search")
        return False
    
    if search_method == 'dob' and not dob:
        helper.log_print("ERROR: Missing patient DOB for DOB search")
        return False
    
    if not dob:
        helper.log_print("ERROR: Missing patient DOB for verification")
        return False
    
    # Step 1: Search patient using specified method
    try:
        if search_method == 'phone':
            helper.log_print(f"Searching patient by Phone + First Name...")
            if not patient_search.search_patient_by_phone_number_and_first_name_ctrl_id(phone, first_name, is_first, clinic_data.get('clinic_name_sf')):
                helper.log_print(f"Patient search by phone failed for {first_name} {last_name}")
                return False
        elif search_method == 'dob':
            helper.log_print(f"Searching patient by DOB + First Name...")
            if not patient_search.search_patient_by_dob_and_first_name_ctrl_id(dob, first_name, is_first, clinic_data.get('clinic_name_sf')):
                helper.log_print(f"Patient search by DOB failed for {first_name} {last_name}")
                return False
        else:
            helper.log_print(f"ERROR: Invalid search method '{search_method}'")
            return False
    except Exception as e:
        if "patient_search_timeout" in str(e):
            # Re-raise timeout to skip clinic
            raise
        elif "eivf_window_not_found" in str(e):
            # Re-raise to trigger restart
            raise Exception("eivf_window_not_found")
        helper.log_print(f"Patient search by {search_method} failed for {first_name} {last_name}")
        return False
    helper.log_print(f"Patient '{first_name} {last_name}' found using {search_method} search!")
    
    # Step 2: Handle alert dialog
    time.sleep(1)
    if patient_search.click_alert_ok_button():
        helper.log_print("Alert handled")
    
    # Step 4: Click New button
    time.sleep(0.5)
    if not notes.click_new_button():
        helper.log_print("Failed to click New button")
        return False
    
    # Step 5: Verify patient in Notes window by DOB (and last name for DOB searches)
    time.sleep(1)
    if search_method == 'dob':
        # For DOB searches, verify both DOB and last name for enhanced accuracy
        if not notes.verify_patient_explorer_match(dob, last_name):
            helper.log_print("ERROR: Patient verification FAILED - DOB or Last Name mismatch")
            raise Exception("patient_verification_failed")
        helper.log_print("Patient verified by DOB and Last Name!")
    else:
        # For phone searches, verify DOB only
        if not notes.verify_patient_explorer_match(dob):
            helper.log_print("ERROR: Patient verification FAILED - DOB mismatch")
            raise Exception("patient_verification_failed")
        helper.log_print("Patient verified by DOB!")
    
    # Step 6: Write note
    time.sleep(0.5)
    if not notes.write_note("CLOUDRX NOTIFICATION", note_data['note']):
        helper.log_print("Failed to write note")
        return False
    
    # Step 7: Save note
    helper.log_print("Waiting 5 seconds before saving...")
    time.sleep(5)
    if not notes.click_save_button():
        helper.log_print("Failed to save note")
        return False
    helper.log_print("Note saved!")
    
    # Step 8: Set color
    note_color = clinic_data.get('color', 'orange') if clinic_data else 'orange'
    color.set_color(note_color)
    
    helper.log_print(f"SUCCESS: Note processed for {first_name} {last_name}")
    return True


def process_clinic(clinic, clinic_notes, patient_report, previous_url=None):
    """Process all notes for a single clinic"""
    helper.log_print(f"\n{'#'*60}")
    helper.log_print(f"CLINIC: {clinic['Clinic_Name']} ({len(clinic_notes)} notes)")
    helper.log_print(f"{'#'*60}")
    
    current_url = clinic['URL']
    skip_config = False
    
    # Check if URL is same as previous clinic
    if previous_url and previous_url == current_url:
        helper.log_print(f"URL unchanged ({current_url}) - skipping configuration change")
        skip_config = True
    
    if skip_config:
        # Just login without config change (eIVF already open from previous clinic)
        app = Application(backend="uia").connect(title="eIVF")
        window = app.window(title="eIVF")
        
        if not login.login(window, clinic['Username'], clinic['Password1'], 
                           clinic['clinic_name_sf'], clinic['URL'], clinic['login_status']):
            helper.log_print("Login failed")
            login.close_application(window)
            return 0, 0
        helper.log_print("Login successful!")
    else:
        # Full process: Open, configure, restart, and login
        app, window = login.open_application(APP_PATH, TARGET_TITLE)
        if not app or not window:
            helper.log_print("Failed to open application")
            raise Exception("Login Issue")
        
        # Change configuration
        if not config_change.change_configuration(window, clinic['URL'], clinic['Facility']):
            helper.log_print("Configuration failed")
            login.close_application(window)
            return 0, 0
        
        # Restart and login
        login.kill_application("eIVF.exe")
        app, window = login.open_application(APP_PATH, TARGET_TITLE)
        
        if not login.login(window, clinic['Username'], clinic['Password1'], 
                           clinic['clinic_name_sf'], clinic['URL'], clinic['login_status']):
            helper.log_print("Login failed")
            login.close_application(window)
            return 0, 0
        helper.log_print("Login successful!")
    
    # Process each note
    success_count = 0
    fail_count = 0
    is_first = True
    
    for idx, note in clinic_notes.iterrows():
        try:
            try:
                helper.check_and_wait_if_paused()
                note_data = data_reader.parse_note_data(note)
                clinic_data = data_reader.parse_clinic_data(clinic)
                
                # Ensure Notes window is closed before processing next patient
                if not is_first:
                    helper.log_print("Closing Notes window before next patient...")
                    notes.close_notes_window()
                    time.sleep(1)
                
                # Get current attempt count for this patient note
                key = f"{note_data['patient_phone']}_{note_data['patient_first_name']}_{note_data['clinic_name']}_{note_data['note_id']}"
                current_attempt = int(patient_report.get(key, {}).get('failure_count', 0)) + 1
                
                # Determine search method based on attempt: 1=dob, 2=phone, 3=dob
                if current_attempt == 2:
                    search_method = 'phone'
                else:
                    search_method = 'dob'
                
                helper.log_print(f"Attempt {current_attempt}/{MAX_PATIENT_FAILURES} using {search_method.upper()} search")
                
                if process_single_note(note_data, clinic_data, is_first, search_method):
                    success_count += 1
                    helper.save_patient_to_report(note_data, 'success', 0)
                    
                    # Update API
                    update_api(note_data['note_id'])
                else:
                    # Track failure count
                    helper.save_patient_to_report(note_data, 'failed', current_attempt)
                    patient_report[key] = {'failure_count': str(current_attempt), 'status': 'failed'}
                    
                    helper.log_print(f"Patient note failed (attempt {current_attempt}/{MAX_PATIENT_FAILURES}) with {search_method.upper()} search")
                    
                    # Screenshot on 2nd and 3rd attempt failures
                    if current_attempt >= 2:
                        helper.take_screenshot(prefix=f"note_entry_failed_attempt{current_attempt}")
                    
                    # Call error API and raise restart exception if max failures reached
                    if current_attempt >= MAX_PATIENT_FAILURES:
                        patient_name = f"{note_data['patient_first_name']} {note_data['patient_last_name']}"
                        log_error_to_portal(
                            patient_name=patient_name,
                            patient_dob=note_data.get('patient_dob', ''),
                            clinic_name=note_data['clinic_name'],
                            emr_system=note_data.get('emr_system', 'eIVF'),
                            error_title=f"Patient Note Failed - All {MAX_PATIENT_FAILURES} attempts exhausted"
                        )
                        fail_count += 1
                        # Raise exception to trigger restart after all attempts exhausted
                        raise RestartEivfException("Note entry failed after all attempts")
                    else:
                        fail_count += 1
                        # Raise exception to trigger restart for retry
                        raise RestartEivfException(f"Note entry failed on attempt {current_attempt}, will retry")
                
                is_first = False
                time.sleep(3)
                
            except Exception as e:
                if "eivf_window_not_found" in str(e):
                    # eIVF window not found - raise restart exception
                    helper.take_screenshot(prefix="eivf_window_not_found")
                    raise RestartEivfException("eIVF window not found")
                    
                elif "patient_search_timeout" in str(e):
                    # Track timeout failure for current note
                    key = f"{note_data['patient_phone']}_{note_data['patient_first_name']}_{note_data['clinic_name']}_{note_data['note_id']}"
                    current_attempt = int(patient_report.get(key, {}).get('failure_count', 0)) + 1
                    helper.save_patient_to_report(note_data, 'timeout', current_attempt)
                    patient_report[key] = {'failure_count': str(current_attempt), 'status': 'timeout'}
                    
                    # Determine which search method was used
                    search_method = 'dob' if current_attempt == 2 else 'phone'
                    
                    helper.log_print(f"Patient search timeout (attempt {current_attempt}/{MAX_PATIENT_FAILURES}) with {search_method.upper()} search")
                    
                    # Screenshot on 2nd and 3rd attempt timeouts
                    if current_attempt >= 2:
                        helper.take_screenshot(prefix=f"patient_search_timeout_attempt{current_attempt}")
                    
                    # Call error API if max failures reached
                    if current_attempt >= MAX_PATIENT_FAILURES:
                        patient_name = f"{note_data['patient_first_name']} {note_data['patient_last_name']}"
                        log_error_to_portal(
                            patient_name=patient_name,
                            patient_dob=note_data.get('patient_dob', ''),
                            clinic_name=note_data['clinic_name'],
                            emr_system=note_data.get('emr_system', 'eIVF'),
                            error_title=f"Patient Search Timeout - All {MAX_PATIENT_FAILURES} attempts exhausted"
                        )
                    
                    fail_count += 1
                    
                    # Raise exception to trigger restart
                    raise RestartEivfException(f"Patient search timeout on attempt {current_attempt}")
                    
                elif "patient_verification_failed" in str(e):
                    # Track verification failures
                    key = f"{note_data['patient_phone']}_{note_data['patient_first_name']}_{note_data['clinic_name']}_{note_data['note_id']}"
                    current_attempt = int(patient_report.get(key, {}).get('failure_count', 0)) + 1
                    helper.save_patient_to_report(note_data, 'verification_failed', current_attempt)
                    patient_report[key] = {'failure_count': str(current_attempt), 'status': 'verification_failed'}
                    
                    # Determine which search method was used
                    search_method = 'dob' if current_attempt == 2 else 'phone'
                    
                    helper.log_print(f"Verification failed (attempt {current_attempt}/{MAX_PATIENT_FAILURES}) with {search_method.upper()} search")
                    
                    # Screenshot on 2nd and 3rd attempt verification failures
                    if current_attempt >= 2:
                        helper.take_screenshot(prefix=f"patient_verification_failed_attempt{current_attempt}")
                    
                    # Call error API if max failures reached
                    if current_attempt >= MAX_PATIENT_FAILURES:
                        patient_name = f"{note_data['patient_first_name']} {note_data['patient_last_name']}"
                        log_error_to_portal(
                            patient_name=patient_name,
                            patient_dob=note_data.get('patient_dob', ''),
                            clinic_name=note_data['clinic_name'],
                            emr_system=note_data.get('emr_system', 'eIVF'),
                            error_title=f"Patient Verification Failed - All {MAX_PATIENT_FAILURES} attempts exhausted"
                        )
                    
                    fail_count += 1
                    
                    # Raise exception to trigger restart
                    raise RestartEivfException(f"Patient verification failed on attempt {current_attempt}")
                else:
                    helper.log_print(f"ERROR: {str(e)}")
                    helper.take_screenshot(prefix="general_error")
                    break
                    
        except RestartEivfException as e:
            # Note entry failed - restart application
            helper.log_print(f"\n{'='*60}")
            helper.log_print(f"Restarting eIVF: {str(e)}")
            helper.log_print(f"{'='*60}\n")
            
            # Take screenshot before restart
            helper.take_screenshot(prefix="restart_eivf")
            
            # Kill eIVF
            login.kill_application("eIVF.exe")
            time.sleep(2)
            
            # Restart application
            helper.log_print("Restarting eIVF...")
            app, window = login.open_application(APP_PATH, TARGET_TITLE)
            if not app or not window:
                helper.log_print("Failed to restart eIVF - skipping remaining notes")
                helper.take_screenshot(prefix="restart_failed")
                return success_count, fail_count
            
            # Re-login
            if not login.login(window, clinic['Username'], clinic['Password1'], 
                               clinic['clinic_name_sf'], clinic['URL'], clinic['login_status']):
                helper.log_print("Re-login failed - skipping remaining notes")
                helper.take_screenshot(prefix="relogin_failed")
                return success_count, fail_count
            
            helper.log_print("eIVF restarted and logged in successfully")
            
            is_first = True  # Reset to first patient mode
            continue  # Continue to next patient
    
    return success_count, fail_count


def main():
    """Main entry point - continuous automation loop"""
    # Initialize
    helper.init_log_file(None)
    helper.init_log_queue_manager()
    #helper.init_heartbeat()
    helper.log_print("=== eIVF Note Bot Started ===")
    
    # Set screen resolution FIRST
    helper.get_and_log_screen_resolution("Before")
    if helper.set_screen_resolution(1920, 1080):
        helper.get_and_log_screen_resolution("After")
        # Wait for resolution to fully apply before starting recording
        time.sleep(2)
    
    # Start recording AFTER resolution is set
    helper.start_recording(output_dir="recordings", fps=5, quality="medium")
    
    try:
        running = True
        while running:
            try:
                # Fetch data from API
                helper.check_and_wait_if_paused()
                clinics, all_notes = data_from_api()
                if clinics is None or all_notes is None:
                    raise Exception("No Data Found")
                
                helper.log_print(f"Fetched {len(clinics)} clinics, {len(all_notes)} notes")
                
                # Filter already processed patients
                patient_report = helper.load_patient_report()
                notes_to_process, skipped = helper.filter_notes_by_report(all_notes, patient_report)
                
                if skipped:
                    helper.log_print(f"Skipping {len(skipped)} already processed patients")
                
                if len(notes_to_process) == 0:
                    helper.log_print("No new notes to process")
                    raise Exception("No Data Found")
                
                helper.log_print(f"Processing {len(notes_to_process)} notes")
                
                # Process each clinic
                total_success = 0
                total_fail = 0
                previous_url = None
                
                for _, clinic in clinics.iterrows():
                    clinic_notes = notes_to_process[
                        notes_to_process['clinic_name'] == clinic['Clinic_Name']
                    ].reset_index(drop=True)
                    
                    if len(clinic_notes) == 0:
                        continue
                    
                    success, fail = process_clinic(clinic, clinic_notes, patient_report, previous_url)
                    total_success += success
                    total_fail += fail
                    
                    # Track current URL for next clinic
                    previous_url = clinic['URL']
                
                # Summary
                helper.log_print(f"\n{'='*60}")
                helper.log_print(f"SESSION SUMMARY: {total_success} success, {total_fail} failed")
                helper.log_print(f"{'='*60}")
                
            except KeyboardInterrupt:
                helper.log_print("\n=== Bot stopped by user ===")
                helper.take_screenshot(prefix="bot_stopped")
                running = False
                
            except Exception as e:
                helper.log_print(f"Error: {str(e)}")
                helper.log_print(traceback.format_exc())
                
                if "No Data" in str(e):
                    helper.log_print("Waiting 30 seconds...")
                    time.sleep(30)
                elif "Login Issue" in str(e):
                    helper.log_print("Retrying login...")
                    helper.take_screenshot(prefix="login_issue")
                else:
                    helper.take_screenshot(prefix="error_main_loop")
                    running = False
    
    finally:
        # Stop recording when bot ends
        helper.log_print("Stopping recording...")
        helper.stop_recording()


if __name__ == "__main__":
    main()

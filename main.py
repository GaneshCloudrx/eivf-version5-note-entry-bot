"""
eIVF Note Entry Bot - Main Orchestrator
24/7 continuous automation for adding patient notes
"""
import time
import traceback

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
from data_from_api import data_from_api, update_api


def process_single_note(note_data, clinic_data, is_first):
    """Process a single patient note entry"""
    helper.log_print(f"\n{'='*60}")
    helper.log_print(f"Processing: {note_data['patient_first_name']} {note_data['patient_last_name']}")
    helper.log_print(f"Phone: {note_data['patient_phone']} | Clinic: {note_data['clinic_name']}")
    helper.log_print(f"{'='*60}")
    
    first_name = note_data['patient_first_name']
    last_name = note_data['patient_last_name']
    phone = note_data['patient_phone']
    
    # Validate required fields
    if not first_name or not phone:
        helper.log_print("ERROR: Missing patient first name or phone")
        return False
    
    # Step 1: Search patient
    try:
        if not patient_search.search_patient_by_phone_number_and_first_name_ctrl_id(phone, first_name, is_first):
            helper.log_print(f"Patient search failed for {first_name} {last_name}")
            return False
    except Exception as e:
        if "patient_search_timeout" in str(e):
            # Re-raise timeout to skip clinic
            raise
        helper.log_print(f"Patient search failed for {first_name} {last_name}")
        return False
    helper.log_print(f"Patient '{first_name} {last_name}' found!")
    
    # Step 2: Handle alert dialog
    time.sleep(1)
    if patient_search.click_alert_ok_button():
        helper.log_print("Alert handled")
    
    # Step 4: Click New button
    time.sleep(0.5)
    if not notes.click_new_button():
        helper.log_print("Failed to click New button")
        return False
    
    # Step 5: Verify patient in Notes window
    time.sleep(1)
    if not notes.verify_patient_explorer_match(first_name, last_name, phone):
        helper.log_print("ERROR: Patient verification FAILED")
        raise Exception("patient_verification_failed")
    helper.log_print("Patient verified!")
    
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


def process_clinic(clinic, clinic_notes, patient_report):
    """Process all notes for a single clinic"""
    helper.log_print(f"\n{'#'*60}")
    helper.log_print(f"CLINIC: {clinic['Clinic_Name']} ({len(clinic_notes)} notes)")
    helper.log_print(f"{'#'*60}")
    
    # Open and configure application
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
                       clinic['clinic_name_sf'], clinic['URL']):
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
            helper.check_and_wait_if_paused()
            note_data = data_reader.parse_note_data(note)
            clinic_data = data_reader.parse_clinic_data(clinic)
            
            if process_single_note(note_data, clinic_data, is_first):
                success_count += 1
                helper.save_patient_to_report(note_data, 'success', 0)
                
                # Update API
                update_api(note_data['note_id'])
            else:
                fail_count += 1
            
            is_first = False
            time.sleep(3)
            
        except Exception as e:
            if "patient_search_timeout" in str(e):
                # Timeout error - skip entire clinic and mark all remaining notes as skipped
                helper.log_print(f"\n{'='*60}")
                helper.log_print("TIMEOUT ERROR: Skipping clinic due to patient search timeout")
                helper.log_print(f"{'='*60}\n")
                
                # Mark current and all remaining notes as skipped with failure count
                remaining_notes = clinic_notes.iloc[idx:].reset_index(drop=True)
                for _, remaining_note in remaining_notes.iterrows():
                    remaining_note_data = data_reader.parse_note_data(remaining_note)
                    key = f"{remaining_note_data['patient_phone']}_{remaining_note_data['patient_first_name']}_{remaining_note_data['clinic_name']}"
                    current_failures = int(patient_report.get(key, {}).get('failure_count', 0)) + 1
                    helper.save_patient_to_report(remaining_note_data, 'skipped', current_failures)
                    patient_report[key] = {'failure_count': str(current_failures), 'status': 'skipped'}
                    helper.log_print(f"Marked {remaining_note_data['patient_first_name']} {remaining_note_data['patient_last_name']} as skipped (attempt {current_failures}/3)")
                
                # Close eIVF and return to continue with next clinic
                try:
                    login.close_application(window)
                except:
                    login.kill_application("eIVF.exe")
                return success_count, fail_count
                
            elif "patient_verification_failed" in str(e):
                # Track verification failures
                key = f"{note_data['patient_phone']}_{note_data['patient_first_name']}_{note_data['clinic_name']}"
                current_failures = int(patient_report.get(key, {}).get('failure_count', 0)) + 1
                helper.save_patient_to_report(note_data, 'verification_failed', current_failures)
                patient_report[key] = {'failure_count': str(current_failures), 'status': 'verification_failed'}
                
                helper.log_print(f"Verification failed ({current_failures}/{helper.MAX_FAILURES})")
                fail_count += 1
            else:
                helper.log_print(f"ERROR: {str(e)}")
                break
    
    return success_count, fail_count


def main():
    """Main entry point - continuous automation loop"""
    # Initialize
    helper.init_log_file(None)
    helper.init_heartbeat()
    helper.start_recording(output_dir="recordings", fps=5, quality="medium")
    helper.log_print("=== eIVF Note Bot Started ===")
    
    # Set screen resolution
    helper.get_and_log_screen_resolution("Before")
    if helper.set_screen_resolution(1920, 1080):
        helper.get_and_log_screen_resolution("After")
    
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
            
            for _, clinic in clinics.iterrows():
                clinic_notes = notes_to_process[
                    notes_to_process['clinic_name'] == clinic['Clinic_Name']
                ].reset_index(drop=True)
                
                if len(clinic_notes) == 0:
                    continue
                
                success, fail = process_clinic(clinic, clinic_notes, patient_report)
                total_success += success
                total_fail += fail
            
            # Summary
            helper.log_print(f"\n{'='*60}")
            helper.log_print(f"SESSION SUMMARY: {total_success} success, {total_fail} failed")
            helper.log_print(f"{'='*60}")
            
        except KeyboardInterrupt:
            helper.log_print("\n=== Bot stopped by user ===")
            helper.stop_recording()
            running = False
            
        except Exception as e:
            helper.stop_recording()
            helper.log_print(f"Error: {str(e)}")
            helper.log_print(traceback.format_exc())
            
            if "No Data" in str(e):
                helper.log_print("Waiting 30 seconds...")
                time.sleep(30)
            elif "Login Issue" in str(e):
                helper.log_print("Retrying login...")
            else:
                running = False


if __name__ == "__main__":
    main()

"""
Main orchestrator - coordinates all modules in sequence
24/7 continuous automation with heartbeat and remote control (pause/resume)
"""
import time
import re
import csv
from config import (
    APP_PATH, TARGET_TITLE, USERNAME, PASSWORD, LOG_FILE_PATH,
    API_BASE_URL, API_AUTH_HEADER, API_SERVER_NAME, API_BOT_NAME, API_TIMEOUT,
    HEARTBEAT_INTERVAL, CLINIC_CODE
)
from modules.utils import init_log_file, close_log_file, log_print
from modules.login import open_application, login, close_application
from modules.configuation_change import change_configuration
from modules.patient_search import search_patient_by_phone_number_and_first_name_coords, click_patient_search_button
from modules.color_addition import set_color, search_patient_by_phone_number_and_first_name
from modules.heartbeat import HeartbeatManager
from modules.patient_search import (
            click_select_button, click_alert_ok_button
        )
from modules.note_addition import (click_new_button,
    write_note, click_save_button, verify_patient_explorer_match)
from modules.csv_reader import parse_note_data, get_clinic_by_name, parse_clinic_data



def process_single_note(note_data, clinic_data, window, is_first):
    """
    Process a single note entry from the CSV file.
    
    Args:
        note_data: Parsed note data dictionary
        clinic_data: Parsed clinic data dictionary (can be None)
        window: The main application window
        
    Returns:
        True if successful, False otherwise
    """
    log_print(f"\n{'='*60}")
    log_print(f"Processing Note ID: {note_data['note_id']}")
    log_print(f"Patient: {note_data['patient_first_name']} {note_data['patient_last_name']}")
    log_print(f"Phone number: {note_data['patient_phone']}")
    log_print(f"Clinic: {note_data['clinic_name']}")
    log_print(f"{'='*60}")
    
    try:
        # Step 1: Search patient by Phone Number and First Name
        patient_first_name = note_data['patient_first_name']
        patient_phone_number = note_data['patient_phone']
        patient_last_name = note_data['patient_last_name']
        
        if not patient_first_name or not patient_phone_number:
            log_print(f"ERROR: Missing required patient data (Phone Number or First Name)")
            return False
        
        log_print(f"Searching for patient: {patient_first_name}, Phone number: {patient_phone_number}")
        if not search_patient_by_phone_number_and_first_name_coords(patient_phone_number, patient_first_name, is_first):
            log_print(f"Patient search failed for {patient_first_name} {patient_last_name}")
            return False
        
        # Step 2: Click Select button
        log_print("Clicking Select button...")
        time.sleep(1)  # Wait for search results to load
        
        if not click_select_button():
            log_print("Failed to click Select button")
            return False
        
        log_print(f"Patient '{patient_first_name} {patient_last_name}' selected!")
        
        # Step 3: Handle Alert dialog if it appears
        time.sleep(1)  # Wait for alert to appear
        if click_alert_ok_button():
            log_print("Alert handled successfully!")
        else:
            log_print("Warning: Could not handle alert dialog (may not have appeared)")
        
        # Step 4: Click New button
        time.sleep(0.5)
        if not click_new_button():
            log_print("Failed to click New button")
            return False
        
        log_print("New button clicked!")
        
        # Step 5: MANDATORY - Verify patient from Notes window before writing
        time.sleep(1)  # Wait for Notes window to load
        log_print("Verifying patient in Notes window (MANDATORY)...")
        if not verify_patient_explorer_match(patient_first_name, patient_last_name, patient_phone_number):
            log_print("ERROR: Patient verification from Notes window FAILED. Skipping this note...")
            return False
        
        log_print("Patient verification PASSED!")
        
        # Step 6: Extract note title and content
        time.sleep(0.5)
        note_title = "Cloudrx Notification"
        note_content = "Test note entry from automation."

        log_print(f"Writing note - Title: '{note_title}', Content: '{note_content}'")
        
        if not write_note(note_title, note_content):
            log_print("Failed to write note")
            return False
        
        log_print("Note (title + content) written successfully!")
        
        # Step 7: Click Save button (wait 5 sec for note to be entered)
        log_print("Waiting 5 seconds before saving...")
        time.sleep(5)
        
        if not click_save_button():
            log_print("Failed to save note")
            return False
        
        log_print("Note saved successfully!")
        
        # Step 8: Set color of the note (if clinic data available)
        if clinic_data and clinic_data.get('color'):
            color = clinic_data['color']
            log_print(f"Setting note color to: {color}")
            set_color(color)
        else:
            # Default color if clinic not found
            log_print("Setting default note color: orange")
            set_color("orange")
        
        log_print(f"SUCCESS: Note processed successfully for {patient_first_name} {patient_last_name}")
        return True
        
    except Exception as e:
        log_print(f"ERROR processing note: {str(e)}")
        import traceback
        log_print(f"Traceback: {traceback.format_exc()}")
        return False


def main():
    """Main function - processes all notes from test_notes.csv"""
    # Initialize log file (uses date-based naming if LOG_FILE_PATH is None)
    # Pass None to use date-based filename, or pass LOG_FILE_PATH to use custom path
    init_log_file(None)  # None = use date-based filename (log_YYYY-MM-DD.txt)

    # Initialize and start heartbeat manager
    # heartbeat_api_url = API_BASE_URL + "rpa_get_bot_status.php"
    # heartbeat_manager = HeartbeatManager(
    #     api_url=heartbeat_api_url,
    #     auth_header=API_AUTH_HEADER,
    #     server_name=API_SERVER_NAME,
    #     bot_name=API_BOT_NAME,
    #     interval=HEARTBEAT_INTERVAL,
    #     timeout=API_TIMEOUT
    # )
    # heartbeat_manager.start()

    log_print("=== Automation started ===")

    try:
        # Step 1: Read all notes from CSV
        log_print("Reading test_notes.csv...")
        with open("test_notes.csv", 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            notes = list(reader)
        
        if not notes:
            log_print("ERROR: No notes found in test_notes.csv. Exiting...")
            return
        
        log_print(f"Found {len(notes)} note(s) to process")
        
        # Step 2: Open application (execute once before main loop)
        #check_and_wait_if_paused(heartbeat_manager)
        app, window = open_application(APP_PATH, TARGET_TITLE)
        if not app or not window:
            log_print("Failed to open application. Exiting...")
            return

        # Step 3: Change configuration (execute once after application opens)
        #check_and_wait_if_paused(heartbeat_manager)
        # log_print("Configuring application settings...")
        # config_success = change_configuration(
        #     window=window,
        #     http_address="https://ww2.fertilityinstitute.com/eivf_provider",
        #     facility_name="FINO"
        #     #facility_name="AFCC;HFIIVF;TFI;IFI;NFI;ARI;DALLAS;AUSTIN;SA;FSH;PFCIVF;RBA;PATHWAYS;ASPIREHFI;CRMORLANDO;MLF;RMG; IVFMD"
        # )

        # if not config_success:
        #     log_print("Configuration change failed, but continuing...")
        # else:
        #     log_print("Configuration updated successfully!")

        # Step 4: Login (execute once after configuration)
        #check_and_wait_if_paused(heartbeat_manager)
        if not login(window, USERNAME, PASSWORD, CLINIC_CODE):
            log_print("Login failed. Exiting...")
            close_application(window)
            return
        log_print("Login successful!")

        # Step 5: Process each note from CSV
        successful_count = 0
        failed_count = 0
        is_first = True
        for idx, note_row in enumerate(notes, start=1):
            log_print(f"\n{'#'*60}")
            log_print(f"Processing note {idx} of {len(notes)}")
            log_print(f"{'#'*60}")
            
            # Parse note data
            note_data = parse_note_data(note_row)
            
            # Find matching clinic
            clinic_name = note_data['clinic_name']
            clinic_row = get_clinic_by_name(clinic_name, "clinic_details.csv")
            clinic_data = parse_clinic_data(clinic_row) if clinic_row else None
            
            if not clinic_data:
                log_print(f"WARNING: Clinic '{clinic_name}' not found in clinic_details.csv")
                log_print("Will use default settings for this note")
            
            # Process the note
            success = process_single_note(note_data, clinic_data, window, is_first)
            
            if success:
                successful_count += 1
                log_print(f"✓ Note {idx} processed successfully")
            else:
                failed_count += 1
                log_print(f"✗ Note {idx} failed to process")
            
            # Wait between notes (except for the last one)
            if idx < len(notes):
                if is_first:
                    is_first = False
                log_print("Waiting 3 seconds before processing next note...")
                time.sleep(3)

        # Summary
        log_print(f"\n{'='*60}")
        log_print("PROCESSING SUMMARY")
        log_print(f"{'='*60}")
        log_print(f"Total notes: {len(notes)}")
        log_print(f"Successful: {successful_count}")
        log_print(f"Failed: {failed_count}")
        log_print(f"{'='*60}")

    except KeyboardInterrupt:
        log_print("\n=== Automation stopped by user ===")
    except Exception as e:
        log_print(f"An error occurred: {str(e)}")
        import traceback
        log_print(f"Traceback: {traceback.format_exc()}")
    finally:
        # Stop heartbeat manager
        #heartbeat_manager.stop()
        # Close log file
        close_log_file()
        log_print("=== Automation stopped ===")

def wait_for_activation(heartbeat_manager):
    """
    Wait until bot is activated by server.
    Checks every 5 seconds if bot should resume.
    """
    log_print("Bot paused by server. Waiting for activation...")
    while not heartbeat_manager.is_bot_active():
        time.sleep(5)  # Check every 5 seconds
    log_print("Bot activated by server. Resuming automation...")

def check_and_wait_if_paused(heartbeat_manager):
    """Check if bot is paused, and wait if it is"""
    if not heartbeat_manager.is_bot_active():
        wait_for_activation(heartbeat_manager)

if __name__ == "__main__":
    main()

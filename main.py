"""
Main orchestrator - coordinates all modules in sequence
24/7 continuous automation with heartbeat and remote control (pause/resume)
"""
import time
from config import (
    APP_PATH, TARGET_TITLE, USERNAME, PASSWORD, LOG_FILE_PATH,
    API_BASE_URL, API_AUTH_HEADER, API_SERVER_NAME, API_BOT_NAME, API_TIMEOUT,
    HEARTBEAT_INTERVAL, CLINIC_CODE
)
from modules.utils import init_log_file, close_log_file, log_print
from modules.login import open_application, login, close_application
from modules.configuation_change import change_configuration
from modules.patient_search import search_patient_by_dob_and_last_name
from modules.color_addition import set_color
from modules.heartbeat import HeartbeatManager

def main():
    """Main function - 24/7 continuous automation with heartbeat and pause/resume"""
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

    log_print("=== Automation started (24/7 continuous mode) ===")

    try:
        # Step 1: Open application (execute once before main loop)
        #check_and_wait_if_paused(heartbeat_manager)
        app, window = open_application(APP_PATH, TARGET_TITLE)
        if not app or not window:
            log_print("Failed to open application. Exiting...")
            return

        # Step 2: Change configuration (execute once after application opens)
        #check_and_wait_if_paused(heartbeat_manager)
        log_print("Configuring application settings...")
        #config_success = change_configuration(
        #    window=window,
        #    http_address="https://ww2.fertilityinstitute.com/eivf_provider",
        #    facility_name="FINO"
        #    #facility_name="AFCC;HFIIVF;TFI;IFI;NFI;ARI;DALLAS;AUSTIN;SA;FSH;PFCIVF;RBA;PATHWAYS;ASPIREHFI;CRMORLANDO;MLF;RMG; IVFMD"
        #)

        #if not config_success:
        #    log_print("Configuration change failed, but continuing...")
        #else:
        #    log_print("Configuration updated successfully!")

        # Step 3: Login (execute once after configuration)

        #check_and_wait_if_paused(heartbeat_manager)
        if not login(window, USERNAME, PASSWORD, CLINIC_CODE):
            log_print("Login failed. Exiting...")
            close_application(window)
            return
        log_print("Login successful!")


        # Step 4: Search patient by DOB and Last Name
        # Patient details for testing
        patient_first_name = "Abbie"
        patient_last_name = "Test"
        patient_dob = "01011980"  # DOB format: MMddyyyy (change this to correct DOB)

        # Search by DOB and Last Name
        if not search_patient_by_dob_and_last_name(window, patient_dob, patient_last_name):
            log_print("Patient search failed. Exiting...")
            return

        # Step 5: Click Select button
        from modules.patient_search import (
            click_select_button, click_alert_ok_button, click_new_button,
            write_note, click_save_button, verify_patient_explorer_match
        )

        log_print("Clicking Select button...")
        time.sleep(1)  # Wait for search results to load

        if click_select_button():
            log_print(f"Patient '{patient_first_name} {patient_last_name}' selected!")

            # Step 6: Handle Alert dialog if it appears
            time.sleep(1)  # Wait for alert to appear
            if click_alert_ok_button():
                log_print("Alert handled successfully!")
            else:
                log_print("Warning: Could not handle alert dialog")

            # Step 7: Click New button
            time.sleep(0.5)
            if click_new_button():
                log_print("New button clicked!")

                # Step 8: MANDATORY - Verify patient from Notes window before writing
                time.sleep(1)  # Wait for Notes window to load
                log_print("Verifying patient in Notes window (MANDATORY)...")
                if not verify_patient_explorer_match(patient_first_name, patient_last_name, patient_dob):
                    log_print("ERROR: Patient verification from Notes window FAILED. Stopping...")
                    return
                log_print("Patient verification PASSED!")

                # Step 9: Enter note title and content
                time.sleep(0.5)
                note_title = "Cloudrx Notification"
                note_content = "Test note entry from automation."

                log_print(f"Writing note - Title: '{note_title}', Content: '{note_content}'")
                if write_note(note_title, note_content):
                    log_print("Note (title + content) written successfully!")

                    # Step 10: Click Save button (wait 5 sec for note to be entered)
                    log_print("Waiting 5 seconds before saving...")
                    time.sleep(5)
                    if click_save_button():
                        log_print("Note saved successfully!")
                        # Step 11: Set color of the note
                        set_color("orange")
                    else:
                        log_print("Failed to save note")
                        return
                else:
                    log_print("Failed to write note")
                    return
            else:
                log_print("Failed to click New button")
                return
        else:
            log_print("Failed to click Select button")
            return



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

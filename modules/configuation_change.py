"""
Configuration change module - handles changing eIVF application settings
"""
from pywinauto import Desktop
import time
from modules.utils import log_print

def change_configuration(window, http_address="https://eivfdfw.aspirefertility.com/eivf_provider", facility_name="AFCC;HFIIVF;TFI;IFI;NFI;ARI;DALLAS;AUSTIN;SA;FSH;PFCIVF;RBA;PATHWAYS;ASPIREHFI;CRMORLANDO;MLF;RMG; IVFMD"):
    """
    Change eIVF application configuration settings.

    Args:
        window: The main eIVF application window
        http_address: New HTTP address to set (optional)
        facility_name: New facility name to set (optional)

    Returns:
        True if successful, False otherwise
    """
    log_print("=== Changing Configuration ===")

    try:
        # Step 1: Click "Option >>" button
        log_print("Clicking Option >> button...")
        option_button = window.child_window(auto_id="4", class_name="ThunderRT6CommandButton")
        option_button.click_input()
        time.sleep(1)  # Wait for options to expand
        log_print("Option button clicked")

        # Step 2: Click "Application Configuration" button
        log_print("Clicking Application Configuration button...")
        config_button = window.child_window(auto_id="3", class_name="ThunderRT6CommandButton")
        config_button.click_input()
        time.sleep(2)  # Wait for configuration window to open
        log_print("Application Configuration button clicked")

        # Find the Application Configuration window
        desktop = Desktop(backend="uia")
        config_window = None
        time.sleep(1)
        
        # Find the Application Configuration window by title
        try:
            config_window = desktop.window(title="Application Configuration")
            config_window.wait('visible', timeout=5)
            log_print("Application Configuration window found")
        except:
            log_print("Could not find Application Configuration window by title, using main window")
            config_window = window

        if not config_window:
            log_print("ERROR: Application Configuration window not found")
            return False

        # Step 3: Change HTTP Address if provided
        if http_address:
            log_print(f"Setting HTTP Address to: {http_address}")
            http_field = config_window.child_window(auto_id="5", class_name="ThunderRT6TextBox")
            http_field.set_focus()
            time.sleep(0.3)
            # Clear existing text using double-click and Backspace (Ctrl+A doesn't work in this window)
            http_field.double_click_input()
            time.sleep(0.2)
            http_field.type_keys("{BACKSPACE}", with_spaces=True)
            time.sleep(0.2)
            # Type new HTTP address
            http_field.type_keys(http_address, with_spaces=True)
            time.sleep(0.5)
            log_print("HTTP Address updated")

        # Step 4: Change Facility Name if provided
        if facility_name:
            log_print(f"Setting Facility Name to: {facility_name}")
            facility_field = config_window.child_window(auto_id="3", class_name="ThunderRT6TextBox")
            facility_field.set_focus()
            time.sleep(0.3)
            # Clear existing text using double-click and Backspace (Ctrl+A doesn't work in this window)
            facility_field.double_click_input()
            time.sleep(0.2)
            facility_field.type_keys("{BACKSPACE}", with_spaces=True)
            time.sleep(0.2)
            # Type new facility name
            facility_field.type_keys(facility_name, with_spaces=True)
            time.sleep(0.5)
            log_print("Facility Name updated")

        # Step 5: Click Save button to apply changes
        log_print("Clicking Save button...")
        try:
            # Find Save button using AutomationId="1" and ClassName="ThunderRT6CommandButton"
            save_button = config_window.child_window(
                auto_id="1", 
                class_name="ThunderRT6CommandButton",
                title="Save"
            )
            save_button.wait('visible', timeout=5)
            save_button.click_input()
            time.sleep(1)
            log_print("Configuration saved")
        except Exception as save_error:
            log_print(f"Could not find Save button with primary method: {save_error}")
            # Fallback: try by title only
            try:
                save_button = config_window.child_window(title="Save", control_type="Button")
                save_button.click_input()
                time.sleep(1)
                log_print("Configuration saved (fallback method)")
            except:
                log_print("Could not find save button, changes may need manual saving")

        log_print("Configuration change completed")
        return True

    except Exception as e:
        log_print(f"Configuration change failed: {str(e)}")
        import traceback
        log_print(f"Traceback: {traceback.format_exc()}")
        return False


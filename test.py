"""
Test script for clicking Results and All checkboxes in eIVF application.
Make sure eIVF is open and a patient is selected before running.
"""
import time
from pywinauto import Application, Desktop

def log_print(message):
    """Simple logging function."""
    print(f"[{time.strftime('%H:%M:%S')}] {message}")

def test_click_checkboxes():
    """
    Test clicking Results checkbox (control_id=31) and All checkbox (control_id=35).
    """
    log_print("=== Testing Checkbox Click ===")
    
    try:
        # Connect to eIVF using win32 backend for VB6 controls
        log_print("Connecting to eIVF application...")
        app_win32 = Application(backend="win32").connect(class_name="ThunderRT6MDIForm", title="eIVF")
        eivf_window = app_win32.window(class_name="ThunderRT6MDIForm", title="eIVF")
        log_print(f"Connected to: {eivf_window.window_text()}")
        
        # Find and click Results checkbox (control_id=31)
        log_print("Finding Results checkbox (control_id=31)...")
        results_checkbox = eivf_window.child_window(
            class_name="ThunderRT6CheckBox",
            control_id=31
        )
        log_print(f"Results checkbox found: {results_checkbox.window_text()}")
        results_checkbox.set_focus()
        results_checkbox.click_input()
        log_print("✔ Results checkbox clicked")
        time.sleep(0.5)
        
        # Find and click All checkbox (control_id=35)
        log_print("Finding All checkbox (control_id=35)...")
        all_checkbox = eivf_window.child_window(
            class_name="ThunderRT6CheckBox",
            control_id=35
        )
        log_print(f"All checkbox found: {all_checkbox.window_text()}")
        all_checkbox.set_focus()
        all_checkbox.click_input()
        log_print("✔ All checkbox clicked")
        time.sleep(0.5)
        
        # Verify All checkbox is checked
        log_print("Verifying All checkbox state...")
        try:
            # Re-find to get fresh state
            all_checkbox = eivf_window.child_window(
                class_name="ThunderRT6CheckBox",
                control_id=35
            )
            state = all_checkbox.get_check_state()
            log_print(f"All checkbox state: {state} (0=unchecked, 1=checked)")
            
            if state == 0:  # Unchecked
                log_print("All checkbox not checked, clicking again...")
                all_checkbox.click_input()
                time.sleep(0.3)
                # Check state again
                state = all_checkbox.get_check_state()
                log_print(f"All checkbox state after second click: {state}")
            
            log_print("✔ All checkbox verification complete")
        except Exception as state_err:
            log_print(f"Could not verify checkbox state: {state_err}")
        
        log_print("=== Test Complete ===")
        return True
        
    except Exception as e:
        log_print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("\n" + "="*60)
    print("eIVF Checkbox Test")
    print("="*60)
    print("Prerequisites:")
    print("  1. eIVF application must be open")
    print("  2. A patient must be selected (Quick Summary visible)")
    print("="*60 + "\n")
    
    input("Press Enter to start test...")
    test_click_checkboxes()


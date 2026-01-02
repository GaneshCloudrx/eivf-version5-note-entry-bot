"""
Test dismiss_update_wizard function

This test checks if the Update Wizard can be detected and dismissed.
The wizard can take up to 30 seconds to appear after eIVF starts.
"""
import sys
import os
# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import time
from modules.login import dismiss_update_wizard, open_application, kill_application
from config import APP_PATH, TARGET_TITLE

def test_update_wizard_handling():
    """
    Test the update wizard detection and dismissal during app startup.
    This simulates the real scenario where wizard might appear.
    """
    print("\n" + "="*70)
    print("TESTING UPDATE WIZARD HANDLING")
    print("="*70)
    print("\nNOTE: Update wizard can take up to 30 seconds to appear")
    print("The open_application function will:")
    print("  1. Check for wizard immediately after start")
    print("  2. Check every second during wait (after 5s)")
    print("  3. Make a final check if login window not found")
    print("="*70 + "\n")
    
    # Clean start
    kill_application("eIVF.exe")
    time.sleep(2)
    
    # Open eIVF - this will handle wizard automatically
    print("Opening eIVF application (max wait: 30 seconds)...")
    print("Watch for '⚠️ Found Update Wizard' messages...\n")
    
    app, window = open_application(APP_PATH, TARGET_TITLE, max_wait_time=30)
    
    print("\n" + "="*70)
    if app and window:
        print("✅ SUCCESS: eIVF opened and login window found!")
        print("="*70)
        print("\nResult: Update wizard was automatically handled (if it appeared)")
        print("The login process can now continue normally.")
    else:
        print("❌ FAILED: Could not open eIVF or find login window")
        print("="*70)
        print("\nThis could mean:")
        print("  - Update wizard appeared but couldn't be dismissed")
        print("  - Application failed to start")
        print("  - Login window took longer than 30s to appear")
    
    print("\n" + "="*70)
    print("Test completed!")
    print("="*70 + "\n")

def test_manual_wizard_check():
    """
    Manually check if update wizard is currently visible.
    Run this if you want to test wizard detection separately.
    """
    print("\n" + "="*70)
    print("MANUAL UPDATE WIZARD CHECK")
    print("="*70 + "\n")
    
    print("Checking for update wizard in current windows...")
    
    if dismiss_update_wizard():
        print("\n✅ Update wizard was found and dismissed!")
    else:
        print("\nℹ️  No update wizard detected in current windows")
    
    print("\n" + "="*70 + "\n")

if __name__ == "__main__":
    print("\n" + "#"*70)
    print("# UPDATE WIZARD DISMISSAL TEST")
    print("#"*70)
    
    # Test 1: Full app startup with wizard handling
    test_update_wizard_handling()
    
    # Optional: Uncomment to test manual wizard detection
    # time.sleep(2)
    # test_manual_wizard_check()


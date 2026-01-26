"""
Test script to click Home button on toolbar pane (leftmost button)
This approach can be used for Patient Explorer clicking as well
"""
import time
from pywinauto import Application

def click_home_button():
    """
    Click Home button on the left toolbar pane.
    Uses coordinate-based clicking since the pane cannot be isolated.
    """
    try:
        # Connect to eIVF main window
        print("Connecting to eIVF...")
        app = Application(backend="uia").connect(title="eIVF", class_name="ThunderRT6MDIForm")
        main_window = app.window(title="eIVF", class_name="ThunderRT6MDIForm")
        
        print(f"Found eIVF window")
        
        # Bring window to front and set focus
        print("Setting focus on eIVF window...")
        main_window.set_focus()
        time.sleep(0.5)
        
        # Maximize if needed
        try:
            main_window.maximize()
            time.sleep(0.3)
        except:
            pass
        
        # Get window rectangle to calculate relative position
        rect = main_window.rectangle()
        print(f"Window rectangle: Left={rect.left}, Top={rect.top}, Right={rect.right}, Bottom={rect.bottom}")
        
        # The pane is at: {l:2 t:81 r:1917 b:104} (from inspect.exe)
        # Home button is leftmost, so click near left edge
        # Relative to window: X = 2 + 20 (offset for button), Y = 81 + 11 (middle of pane height 23)
        
        # Absolute coordinates
        click_x = rect.left + 22  # 2 (pane left) + 20 (button offset)
        click_y = rect.top + 92   # 81 (pane top) + 11 (half of 23px height)
        
        print(f"Clicking Home button at absolute coords: ({click_x}, {click_y})")
        print(f"Relative to window: (22, 92)")
        
        # Click using relative coordinates (more reliable)
        main_window.click_input(coords=(22, 92))
        time.sleep(1)
        
        print("✓ Home button clicked successfully!")
        
        # Press right arrow key after 1 second
        print("Pressing Right arrow key...")
        main_window.type_keys("{RIGHT}")
        time.sleep(0.5)
        
        print("✓ Right arrow key pressed!")
        return True
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def click_patient_explorer_alternative():
    """
    Alternative method to click Patient Explorer using coordinate approach.
    Can replace sidebar clicking for IVFMD-type clinics.
    
    Key insight: If Patient Explorer is at a fixed position in the toolbar/pane,
    we can click it using coordinates relative to the main window.
    """
    try:
        # Connect to eIVF main window
        print("\n=== Testing Patient Explorer Click (Coordinate Method) ===")
        app = Application(backend="uia").connect(title="eIVF", class_name="ThunderRT6MDIForm")
        main_window = app.window(title="eIVF", class_name="ThunderRT6MDIForm")
        
        # Bring window to front and set focus
        main_window.set_focus()
        time.sleep(0.5)
        
        rect = main_window.rectangle()
        print(f"Window rectangle: Left={rect.left}, Top={rect.top}")
        
        # Patient Explorer is typically further right on the toolbar
        # Adjust these coordinates based on actual position
        # Example: If it's the 5th button, offset would be ~5 * 30px = 150px from left
        
        click_x_relative = 150  # Adjust based on actual button position
        click_y_relative = 92   # Same Y as other toolbar buttons
        
        print(f"Clicking Patient Explorer at relative coords: ({click_x_relative}, {click_y_relative})")
        
        main_window.click_input(coords=(click_x_relative, click_y_relative))
        time.sleep(0.5)
        
        print("✓ Patient Explorer clicked successfully!")
        return True
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("=" * 60)
    print("Test: Click Home Button (Leftmost on Toolbar)")
    print("=" * 60)
    
    # Test 1: Click Home button
    success = click_home_button()
    
    if success:
        print("\n✓ Test passed - Home button clicked")
        print("\nApproach Analysis:")
        print("=" * 60)
        print("✓ Uses relative coordinates from main window")
        print("✓ Leftmost button = (22, 92) relative to window")
        print("✓ Works without isolating the pane control")
        print("✓ Can be adapted for Patient Explorer button")
        print("\nFor Patient Explorer:")
        print("- Find its X position on toolbar (e.g., 150px, 200px)")
        print("- Use same Y coordinate (92)")
        print("- Click: main_window.click_input(coords=(X, 92))")
    else:
        print("\n✗ Test failed - Check eIVF is running")
    
    # Uncomment to test Patient Explorer alternative
    # time.sleep(2)
    # click_patient_explorer_alternative()


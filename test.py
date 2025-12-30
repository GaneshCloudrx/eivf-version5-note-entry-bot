from pywinauto import Application

# Connect to the eIVF .Net application using UIA backend (for WinForms)
app = Application(backend="uia").connect(title="eIVF .Net")

# Get the main window
main_window = app.window(title="eIVF .Net")

# Find the verification code text box by AutomationId
verf_code_box = main_window.child_window(auto_id="verfCode", control_type="Edit")

# Type the code into the text box
verf_code_box.type_keys("12345", with_spaces=True)

# Find and click the Verify button
verify_button = main_window.child_window(auto_id="button1", control_type="Button")
verify_button.click()

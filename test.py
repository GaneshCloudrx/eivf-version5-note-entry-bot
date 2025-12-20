from pywinauto import Application

# Connect to eIVF application using win32 backend
# Use class_name to avoid ambiguity with multiple "eIVF" windows
app = Application(backend="win32").connect(class_name="ThunderRT6MDIForm", title="eIVF")

# Find the Patient Search window (note: title has spaces around it)
patient_search = app.window(class_name="ThunderRT6FormDC", title_re=".*Patient Search.*")
patient_search.wait("visible", timeout=10)
print(f"Found Patient Search window: {patient_search.window_text()}")

# Find and click the Phone Number radio button
# AutomationId="7", ClassName="ThunderRT6OptionButton"
phone_number_radio = patient_search.child_window(class_name="ThunderRT6OptionButton", title="Phone  Number")
phone_number_radio.click()
print("Clicked Phone Number radio button")

import time
time.sleep(0.5)

# Find and click the text box (control_id=14, ClassName="ThunderRT6TextBox")
# In win32 backend, use control_id instead of auto_id
search_textbox = patient_search.child_window(class_name="ThunderRT6TextBox", control_id=14)
search_textbox.set_focus()
# Clear existing content with Ctrl+A + Backspace, then type new text
search_textbox.type_keys("^a{BACKSPACE}4155553333")
print("Typed in search text box")

time.sleep(0.5)

# Click the search icon button (control_id=13, ClassName="ThunderRT6CommandButton")
search_button = patient_search.child_window(class_name="ThunderRT6CommandButton", control_id=13)
search_button.click()
print("Clicked search button")

time.sleep(0.5)

# Re-fetch the Patient Search window after search to get fresh reference
patient_search = app.window(class_name="ThunderRT6FormDC", title_re=".*Patient Search.*")
patient_search.wait("visible", timeout=10)

first_name_radio = patient_search.child_window(class_name="ThunderRT6OptionButton", control_id=18)
first_name_radio.click_input()
print("Clicked First Name radio button")

# Find and click the text box (control_id=14, ClassName="ThunderRT6TextBox")
# In win32 backend, use control_id instead of auto_id
search_textbox = patient_search.child_window(class_name="ThunderRT6TextBox", control_id=14)
search_textbox.set_focus()
# Clear existing content with Ctrl+A + Backspace, then type new text
search_textbox.type_keys("^a{BACKSPACE}John")
print("Typed in search text box")



time.sleep(0.5)
# Click the search icon button (control_id=13, ClassName="ThunderRT6CommandButton")
search_button = patient_search.child_window(class_name="ThunderRT6CommandButton", control_id=4)
search_button.click()
print("Clicked search button")
import time
from pywinauto import Application, Desktop

# Find the Notes window from Desktop and get its process ID
desktop = Desktop(backend="win32")

notes_pid = None
notes_title = None
for win in desktop.windows():
    try:
        title = win.window_text()
        if "Notes" in title and "Quick Summary" in title:
            notes_pid = win.process_id()
            notes_title = title
            print(f"Found Notes window: {title}, PID: {notes_pid}")
            break
    except:
        pass

if notes_pid:
    # Connect to the Notes application using its PID
    app = Application(backend="win32").connect(process=notes_pid)
    notes_window = app.window(title_re=".*Notes.*Quick Summary.*")
    
    # Find lblTitle label - the one that starts with "Quick Notes:"
    lbl_title = notes_window.child_window(class_name_re=".*WindowsForms10\\.STATIC.*", title_re=".*Quick Notes.*")
    patient_info = lbl_title.window_text()
    print(f"Patient Info: {patient_info}")
else:
    print("Notes window not found")

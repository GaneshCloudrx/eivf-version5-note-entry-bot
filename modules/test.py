from pywinauto import Application, Desktop

desktop = Desktop(backend="uia")

print("Finding main eIVF window (ThunderRT6MDIForm)...")

# Find the main eIVF window
for win in desktop.windows():
    try:
        win_title = win.window_text()
        win_class = win.element_info.class_name
        
        if win_title.lower() == "eivf" and win_class == "ThunderRT6MDIForm":
            process_id = win.element_info.process_id
            rect = win.rectangle()
            print(f"Found: '{win_title}' (Class: {win_class}, PID: {process_id})")
            print(f"Size: {rect.width()} x {rect.height()}")
            
            # Connect to application properly
            app = Application(backend="uia").connect(process=process_id)
            # Use title_re for case-insensitive match or use exact title from win_title
            main_window = app.window(title=win_title, class_name="ThunderRT6MDIForm")
            
            # Print all child elements
            print("\n" + "="*80)
            print("ALL CHILD ELEMENTS:")
            print("="*80 + "\n")
            
            main_window.print_control_identifiers(depth=8)
            break
    except Exception as e:
        print(f"Error: {e}")
        pass

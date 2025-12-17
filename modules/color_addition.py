from pywinauto import Application, Desktop
import time
from modules.utils import log_print



def get_desktop():
    """Get Desktop instance with UIA backend."""
    return Desktop(backend="uia")


def set_color(color, window_title="eivf", window_class="ThunderRT6MDIForm"):
    color_coordinates = {"red": (1748,922), "blue": (1772,922), "pink": (1796,922), "black": (1820,922), "green": (1844,922), "purple": (1868,922), "orange": (1892,922)}
    try:
        desktop = get_desktop()
        for win in desktop.windows():
            try:
                win_title = win.window_text()
                win_class = win.element_info.class_name
                
                # Skip system windows to reduce log noise
                system_windows = ["taskbar", "shell_traywnd", "activate windows", "worker window"]
                if any(sys_win in win_title.lower() for sys_win in system_windows):
                    continue
                
                if win_title.lower() == window_title and win_class == window_class:
                    process_id = win.element_info.process_id
                    app = Application(backend="uia").connect(process=process_id)
                    main_window = app.window(title=win_title, class_name=win_class)
                    log_print(f"1. Found main eIVF window (Title: '{win_title}', Class: {win_class}, PID: {process_id})")
                    main_window.click_input(coords=(460,232))
                    time.sleep(0.1)
                    log_print("2. Selected the recently added comment")
                    main_window.click_input(coords=color_coordinates[color])
                    time.sleep(0.1)
                    log_print(f"3. Selected the color: {color}")
                    time.sleep(0.1)
                    element = main_window.child_window(auto_id="25", class_name="ThunderRT6CommandButton")
                    element.click_input()
                    log_print("4. Saved the changes")
                    return True
            except Exception:
                # Skip windows that can't be accessed (common for system windows)
                continue
        log_print("Could not find eIVF window for color setting")
        return False
    except Exception as e:
        log_print(f"Error setting color: {e}")
        return False

def search_patient_by_phone_number_and_first_name(phone_number, first_name, window_title="eivf", window_class="ThunderRT6MDIForm"):
    try:
        desktop = get_desktop()
        for win in desktop.windows():
            win_title = win.window_text()
            win_class = win.element_info.class_name
            if win_title.lower() == window_title and win_class == window_class:
                process_id = win.element_info.process_id
                app = Application(backend="uia").connect(process=process_id)
                main_window = app.window(title=win_title, class_name=win_class)
                log_print(f"1. Found main eIVF window (Title: '{win_title}', Class: {win_class}, PID: {process_id})")
                element = main_window.child_window(auto_id="7", class_name="ThunderRT6OptionButton")
                element.click_input()
                log_print("2. Clicked on the phone number to enter number")
                element = main_window.child_window(auto_id="14", class_name="ThunderRT6TextBox")
                element.type_keys(phone_number)
                log_print(f"3. Entered the phone number: {phone_number}")
                element = main_window.child_window(auto_id="13", class_name="ThunderRT6CommandButton")
                element.click_input()
                log_print("4. Clicked on the search button")
                element = main_window.child_window(auto_id="18", class_name="ThunderRT6OptionButton")
                element.click_input()
                log_print("5. Clicked on the first name radio button")
                element = main_window.child_window(auto_id="14", class_name="ThunderRT6TextBox")
                element.type_keys(first_name)
                log_print(f"6. Entered the first name: {first_name}")
                element = main_window.child_window(auto_id="13", class_name="ThunderRT6CommandButton")
                element.click_input()
                log_print("7. Clicked on the search button")
                # element = main_window.child_window(auto_id="4", class_name="ThunderRT6CommandButton")
                # element.click_input()
                # log_print("8. Clicked on the select button")
                # element = main_window.child_window(auto_id="3", class_name="ThunderRT6CommandButton")
                # element.click_input()
                # log_print("9. Clicked on the OK button")
                return True
            else:
                log_print(f"Window not found: {win_title}, {win_class}")
        return False
    except Exception as e:
        log_print(f"Error: {e}")
        return False

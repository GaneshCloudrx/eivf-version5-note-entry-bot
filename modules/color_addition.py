"""
Color addition module - handles setting note colors in eIVF
"""
import time
from pywinauto import Application, Desktop

import modules.helper as helper



def get_desktop():
    """Get Desktop instance with UIA backend."""
    return Desktop(backend="uia")


def set_color(color, window_title="eivf", window_class="ThunderRT6MDIForm"):
    # Skip if color is black (default color, no need to click)
    if color and color.lower() == "black":
        helper.log_print("Color is black (default), skipping color selection")
        return True
    
    color_coordinates = {"red": (1748,922), "blue": (1772,922), "pink": (1796,922), "black": (1820,922), "green": (1844,922), "purple": (1868,922), "orange": (1892,922)}
    
    # Dynamic wait for eIVF window (up to 10 seconds)
    timeout = 10
    time.sleep(5)
    start_time = time.time()
    
    while (time.time() - start_time) < timeout:
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
                    
                    if win_title.lower() == window_title.lower() and win_class.lower() == window_class.lower():
                        process_id = win.element_info.process_id
                        app = Application(backend="uia").connect(process=process_id)
                        main_window = app.window(title=win_title, class_name=win_class)
                        time.sleep(1)
                        helper.log_print(f"1. Found main eIVF window (Title: '{win_title}', Class: {win_class}, PID: {process_id})")
                        main_window.click_input(coords=(460,232))
                        time.sleep(0.1)
                        helper.log_print("2. Selected the recently added comment")
                        main_window.click_input(coords=color_coordinates[color])
                        time.sleep(0.1)
                        helper.log_print(f"3. Selected the color: {color}")
                        time.sleep(0.1)
                        element = main_window.child_window(auto_id="25", class_name="ThunderRT6CommandButton")
                        element.click_input()
                        helper.log_print("4. Saved the changes")
                        time.sleep(1)

                        helper.log_print(f"1. Found main eIVF window (Title: '{win_title}', Class: {win_class}, PID: {process_id})")
                        main_window.click_input(coords=(460,232))
                        time.sleep(0.1)
                        helper.log_print("2. Selected the recently added comment")
                        main_window.click_input(coords=color_coordinates[color])
                        time.sleep(0.1)
                        helper.log_print(f"3. Selected the color: {color}")
                        time.sleep(0.1)
                        element = main_window.child_window(auto_id="25", class_name="ThunderRT6CommandButton")
                        element.click_input()
                        helper.log_print("4. Saved the changes")
                        time.sleep(1)
                        
                        return True
                except Exception:
                    # Skip windows that can't be accessed (common for system windows)
                    continue
        except Exception:
            pass
        
        time.sleep(0.5)
    
    helper.log_print(f"Could not find eIVF window for color setting after {timeout}s")
    return False
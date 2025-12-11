"""
Test script to scan for 'Patient Explorer' text in whole eIVF window
"""
from pywinauto import Application, Desktop
import time

def get_eivf_window():
    """Find eIVF window"""
    desktop = Desktop(backend="uia")
    
    for win in desktop.windows():
        try:
            win_title = win.window_text()
            win_class = win.element_info.class_name
            if win_title.lower() == "eivf" and win_class == "ThunderRT6MDIForm":
                process_id = win.element_info.process_id
                print(f"Found eIVF window - PID: {process_id}")
                
                app = Application(backend="uia").connect(process=process_id)
                main_window = app.window(title=win_title, class_name="ThunderRT6MDIForm")
                return app, main_window, process_id
        except:
            pass
    return None, None, None


def scan_for_text(main_window, search_text):
    """Scan ALL elements for text containing search_text"""
    print(f"\n" + "="*80)
    print(f"SCANNING FOR '{search_text}' IN ALL ELEMENTS:")
    print("="*80 + "\n")
    
    search_lower = search_text.lower()
    found_elements = []
    
    try:
        descendants = main_window.descendants()
        print(f"Total elements to scan: {len(descendants)}\n")
        
        for i, element in enumerate(descendants):
            try:
                name = element.window_text()
                
                # Check if search text is in name
                if name and search_lower in name.lower():
                    control_type = element.element_info.control_type
                    auto_id = element.element_info.automation_id
                    class_name = element.element_info.class_name
                    rect = element.rectangle()
                    
                    print(f">>> FOUND [{i}]: '{name}'")
                    print(f"    ControlType: {control_type}")
                    print(f"    AutomationId: {auto_id}")
                    print(f"    ClassName: {class_name}")
                    print(f"    Bounds: L={rect.left}, T={rect.top}, R={rect.right}, B={rect.bottom}")
                    print()
                    
                    found_elements.append({
                        'index': i,
                        'name': name,
                        'control_type': control_type,
                        'auto_id': auto_id,
                        'class_name': class_name,
                        'element': element
                    })
            except:
                pass
        
        return found_elements
    except Exception as e:
        print(f"Error: {e}")
        return []


def scan_with_win32(process_id, search_text):
    """Scan using win32 backend"""
    print(f"\n" + "="*80)
    print(f"SCANNING WITH WIN32 BACKEND FOR '{search_text}':")
    print("="*80 + "\n")
    
    search_lower = search_text.lower()
    
    try:
        app = Application(backend="win32").connect(process=process_id)
        main_window = app.window(class_name="ThunderRT6MDIForm")
        
        descendants = main_window.descendants()
        print(f"Total elements (win32): {len(descendants)}\n")
        
        for i, element in enumerate(descendants):
            try:
                name = element.window_text()
                if name and search_lower in name.lower():
                    print(f">>> FOUND [{i}]: '{name}'")
                    print(f"    Class: {element.class_name()}")
                    print(f"    Rectangle: {element.rectangle()}")
                    print()
            except:
                pass
    except Exception as e:
        print(f"Error with win32 backend: {e}")


def print_all_text_elements(main_window):
    """Print ALL elements that have any text"""
    print(f"\n" + "="*80)
    print(f"ALL ELEMENTS WITH TEXT:")
    print("="*80 + "\n")
    
    try:
        descendants = main_window.descendants()
        
        for i, element in enumerate(descendants):
            try:
                name = element.window_text()
                if name:  # Only print elements with text
                    control_type = element.element_info.control_type
                    class_name = element.element_info.class_name
                    rect = element.rectangle()
                    
                    print(f"[{i}] '{name}'")
                    print(f"    Type: {control_type}, Class: {class_name}")
                    print(f"    Bounds: L={rect.left}, T={rect.top}, R={rect.right}, B={rect.bottom}")
                    print()
            except:
                pass
    except Exception as e:
        print(f"Error: {e}")


def main():
    print("="*60)
    print("eIVF Text Scanner - Looking for 'Patient Explorer'")
    print("="*60)
    
    app, main_window, process_id = get_eivf_window()
    
    if not main_window:
        print("Could not find eIVF window!")
        return
    
    # Scan for "Patient Explorer"
    found = scan_for_text(main_window, "Patient Explorer")
    
    # Also try "Patient"
    if not found:
        print("\nNo exact match, trying 'Patient'...")
        found = scan_for_text(main_window, "Patient")
    
    # Also try "Explorer"
    if not found:
        print("\nNo match for 'Patient', trying 'Explorer'...")
        found = scan_for_text(main_window, "Explorer")
    
    # Try win32 backend
    scan_with_win32(process_id, "Patient")
    
    # Print all elements with text for reference
    print_all_text_elements(main_window)
    
    # Summary
    print("\n" + "="*80)
    print("SUMMARY:")
    print("="*80)
    if found:
        print(f"Found {len(found)} matching elements!")
        for elem in found:
            print(f"  - '{elem['name']}' (Type: {elem['control_type']})")
    else:
        print("No elements found with 'Patient Explorer' text.")
        print("The menu items may be rendered as graphics inside the ATL control.")


if __name__ == "__main__":
    main()

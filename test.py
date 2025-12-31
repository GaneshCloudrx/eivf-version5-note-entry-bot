"""Test script for close_notes_window function"""
from modules.note_addition import close_notes_window

if __name__ == "__main__":
    print("\n=== Testing Close Notes Window ===\n")
    result = close_notes_window()
    if result:
        print("✓ Notes window closed successfully")
    else:
        print("✗ Failed to close Notes window")

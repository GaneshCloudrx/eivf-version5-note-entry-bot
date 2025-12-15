"""
CSV Reader module - handles reading patient notes and clinic details from CSV files
"""
import csv
import os
from modules.utils import log_print


def read_csv_file(file_path):
    """
    Read a CSV file and return list of dictionaries.
    
    Args:
        file_path: Path to the CSV file
        
    Returns:
        List of dictionaries where each dict represents a row
    """
    if not os.path.exists(file_path):
        log_print(f"ERROR: CSV file not found: {file_path}")
        return []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            return list(reader)
    except Exception as e:
        log_print(f"ERROR reading CSV file {file_path}: {str(e)}")
        return []


def get_patient_notes(notes_file="test_notes.csv"):
    """
    Read patient notes from test_notes.csv file.
    
    Args:
        notes_file: Path to the notes CSV file
        
    Returns:
        List of note dictionaries with keys:
        - autoIncrementID, note_id, patient_first_name, patient_last_name,
        - patient_dob, patient_phone, emr_system, note, clinic_name, created
    """
    log_print(f"Reading patient notes from: {notes_file}")
    notes = read_csv_file(notes_file)
    log_print(f"Found {len(notes)} patient note(s)")
    return notes


def get_clinic_details(clinic_file="clinic_details.csv"):
    """
    Read clinic details from clinic_details.csv file.
    
    Args:
        clinic_file: Path to the clinic details CSV file
        
    Returns:
        List of clinic dictionaries with keys:
        - Clinic_Id, Clinic_Name, clinic_name_sf, URL, Facility,
        - Username, Password1, Color, login_status, note_bot_machine,
        - lamar_bot_machine, ins_pulling_bot_machine
    """
    log_print(f"Reading clinic details from: {clinic_file}")
    clinics = read_csv_file(clinic_file)
    log_print(f"Found {len(clinics)} clinic(s)")
    return clinics


def get_clinic_by_name(clinic_name, clinic_file="clinic_details.csv"):
    """
    Find a clinic by its name from the clinic_details.csv file.
    
    Args:
        clinic_name: Name of the clinic to find (matches Clinic_Name column)
        clinic_file: Path to the clinic details CSV file
        
    Returns:
        Clinic dictionary if found, None otherwise
    """
    clinics = get_clinic_details(clinic_file)
    
    for clinic in clinics:
        # Match by Clinic_Name (exact or partial match)
        if clinic.get('Clinic_Name', '').strip() == clinic_name.strip():
            log_print(f"Found clinic: {clinic.get('Clinic_Name')}")
            return clinic
        # Also try partial match (clinic_name contains the search term)
        if clinic_name.strip() in clinic.get('Clinic_Name', '').strip():
            log_print(f"Found clinic (partial match): {clinic.get('Clinic_Name')}")
            return clinic
    
    log_print(f"Clinic not found: {clinic_name}")
    return None


def parse_note_data(note_row):
    """
    Parse a note row and extract structured data.
    
    Args:
        note_row: Dictionary from CSV row
        
    Returns:
        Dictionary with parsed note data
    """
    # Parse DOB - convert from MM/DD/YYYY to MMddyyyy format
    dob_original = note_row.get('patient_dob', '')
    dob_formatted = ''
    if dob_original:
        try:
            # Assuming format is MM/DD/YYYY
            parts = dob_original.split('/')
            if len(parts) == 3:
                month, day, year = parts
                dob_formatted = f"{month.zfill(2)}{day.zfill(2)}{year}"
        except Exception as e:
            log_print(f"Error parsing DOB '{dob_original}': {str(e)}")
            dob_formatted = dob_original.replace('/', '')
    
    return {
        'auto_increment_id': note_row.get('autoIncrementID', ''),
        'note_id': note_row.get('note_id', ''),
        'patient_first_name': note_row.get('patient_first_name', ''),
        'patient_last_name': note_row.get('patient_last_name', ''),
        'patient_dob': dob_formatted,  # MMddyyyy format
        'patient_dob_original': dob_original,  # Original format
        'patient_phone': note_row.get('patient_phone', ''),
        'emr_system': note_row.get('emr_system', ''),
        'note': note_row.get('note', ''),
        'clinic_name': note_row.get('clinic_name', ''),
        'created': note_row.get('created', '')
    }


def parse_clinic_data(clinic_row):
    """
    Parse a clinic row and extract structured data.
    
    Args:
        clinic_row: Dictionary from CSV row
        
    Returns:
        Dictionary with parsed clinic data
    """
    return {
        'clinic_id': clinic_row.get('Clinic_Id', ''),
        'clinic_name': clinic_row.get('Clinic_Name', ''),
        'clinic_name_sf': clinic_row.get('clinic_name_sf', ''),
        'url': clinic_row.get('URL', ''),
        'facility': clinic_row.get('Facility', ''),
        'username': clinic_row.get('Username', ''),
        'password': clinic_row.get('Password1', ''),
        'color': clinic_row.get('Color', '').lower(),  # lowercase for color matching
        'login_status': clinic_row.get('login_status', ''),
        'note_bot_machine': clinic_row.get('note_bot_machine', ''),
        'lamar_bot_machine': clinic_row.get('lamar_bot_machine', ''),
        'ins_pulling_bot_machine': clinic_row.get('ins_pulling_bot_machine', '')
    }


def get_note_with_clinic_details(notes_file="test_notes.csv", clinic_file="clinic_details.csv"):
    """
    Read all notes and match with their respective clinic details.
    
    Args:
        notes_file: Path to the notes CSV file
        clinic_file: Path to the clinic details CSV file
        
    Returns:
        List of tuples: (parsed_note_data, parsed_clinic_data)
        If clinic not found for a note, clinic_data will be None
    """
    notes = get_patient_notes(notes_file)
    result = []
    
    for note_row in notes:
        note_data = parse_note_data(note_row)
        clinic_name = note_data['clinic_name']
        
        # Find matching clinic
        clinic_row = get_clinic_by_name(clinic_name, clinic_file)
        clinic_data = parse_clinic_data(clinic_row) if clinic_row else None
        
        if clinic_data:
            log_print(f"Matched note for patient '{note_data['patient_first_name']} {note_data['patient_last_name']}' "
                     f"with clinic '{clinic_data['clinic_name']}'")
        else:
            log_print(f"WARNING: No clinic found for note with clinic_name: '{clinic_name}'")
        
        result.append((note_data, clinic_data))
    
    return result


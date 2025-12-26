"""
Data reader module - parses patient notes and clinic data
"""
import modules.helper as helper


def parse_note_data(note_row):
    """Parse a note row and extract structured data."""
    dob_original = note_row['patient_dob']
    dob_formatted = ''
    if dob_original:
        try:
            parts = dob_original.split('/')
            if len(parts) == 3:
                month, day, year = parts
                dob_formatted = f"{month.zfill(2)}{day.zfill(2)}{year}"
        except Exception as e:
            helper.log_print(f"Error parsing DOB '{dob_original}': {str(e)}")
            dob_formatted = dob_original.replace('/', '')
    
    return {
        'note_id': note_row['note_id'],
        'patient_first_name': note_row['patient_first_name'],
        'patient_last_name': note_row['patient_last_name'],
        'patient_dob': dob_formatted,
        'patient_dob_original': dob_original,
        'patient_phone': note_row['patient_phone'],
        'emr_system': note_row['emr_system'],
        'note': note_row['note'],
        'clinic_name': note_row['clinic_name'],
        'created': note_row['created']
    }


def parse_clinic_data(clinic_row):
    """Parse a clinic row and extract structured data."""
    return {
        'clinic_id': clinic_row['Clinic_Id'],
        'clinic_name': clinic_row['Clinic_Name'],
        'clinic_name_sf': clinic_row['clinic_name_sf'],
        'url': clinic_row['URL'],
        'facility': clinic_row['Facility'],
        'username': clinic_row['Username'],
        'password': clinic_row['Password1'],
        'color': clinic_row['Color'].lower(),
        'login_status': clinic_row['login_status'],
        'note_bot_machine': clinic_row['note_bot_machine'],
        'lamar_bot_machine': clinic_row['lamar_bot_machine'],
        'ins_pulling_bot_machine': clinic_row['ins_pulling_bot_machine']
    }

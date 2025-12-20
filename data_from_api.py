from modules.utils import log_print
from modules.api_integration import get_clinic_details, get_login_token, get_emr_notes
import pandas as pd
import base64
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad
from config import MACHINE_NAME, API_BASE_URL, ADMIN_EMAIL, ADMIN_PASSWORD


def decrypt_password(encrypted_text):
    """
    Decrypt AES-256-CBC encrypted password.
    
    Args:
        encrypted_text: The encrypted password string (Base64 encoded)
    
    Returns:
        Decrypted plaintext password
    """
    key_string = "EIVFBOTCSV0000JHKFGDERFFL1234567"  # 32 chars for AES-256
    
    # Step 1: Outer Base64 decode
    outer_decoded = base64.b64decode(encrypted_text)
    
    # Step 2: Split into Base64 ciphertext and raw IV using "::" separator
    separator = b"::"
    sep_index = outer_decoded.find(separator)
    
    if sep_index == -1:
        raise Exception("Invalid encrypted format")
    
    b64_ciphertext = outer_decoded[:sep_index]
    iv = outer_decoded[sep_index + len(separator):]
    
    # Step 3: Inner Base64 decode
    ciphertext = base64.b64decode(b64_ciphertext)
    
    # Step 4: AES-256-CBC decrypt
    key = key_string.encode('utf-8')
    
    cipher = AES.new(key, AES.MODE_CBC, iv)
    decrypted_bytes = cipher.decrypt(ciphertext)
    
    # Remove PKCS7 padding
    plaintext = unpad(decrypted_bytes, AES.block_size).decode('utf-8')
    print(plaintext)
    
    return plaintext

def data_from_api():
    try:
        log_print(f"API DATA: 1. Fetching clinic details")
        clinic_details = get_clinic_details()
        if clinic_details:
            clinic_data = clinic_details['data']
            log_print(f"API DATA: 2. Clinic data fetched successfully with {len(clinic_data)} clinics")
            clinics = pd.DataFrame(clinic_data, columns=['Clinic_Id', 'Username', 'Password1', 'clinic_name_sf', 'Clinic_Name', 'URL', 'Facility', 'Color', 'login_status', 'note_bot_machine', 'lamar_bot_machine', 'ins_pulling_bot_machine'])
            clinics = clinics[clinics['note_bot_machine'] == MACHINE_NAME].reset_index(drop=True)
            log_print(f"API DATA: 3. Filtered clinics for machine {MACHINE_NAME} with {len(clinics)} clinics")
            
            # Decrypt Password1 column
            for index, row in clinics.iterrows():
                if pd.notna(row['Password1']) and row['Password1'] != '':
                    try:
                        decrypted_password = decrypt_password(row['Password1'])
                        clinics.at[index, 'Password1'] = decrypted_password
                    except Exception as e:
                        log_print(f"API DATA: Warning - Failed to decrypt password for clinic {row['Clinic_Name']}: {str(e)}")
            log_print(f"API DATA: 3a. Passwords decrypted successfully")
            if len(clinics) > 0:
                log_print(f"API DATA: 4. Fetching token for admin")
                status, token = get_login_token(API_BASE_URL, ADMIN_EMAIL, ADMIN_PASSWORD)
                if status:
                    log_print(f"API DATA: 5. Token fetched successfully")
                    status, note_details = get_emr_notes(API_BASE_URL, token)  
                    if status:
                        log_print(f"API DATA: 6. Notes fetched successfully with {len(note_details['data'])} notes")
                        notes = pd.DataFrame(note_details['data'], columns=['note_id', 'patient_id', 'note', 'author', 'created', 'patient_first_name', 'patient_last_name', 'patient_dob', 'patient_phone', 'clinic_name', 'emr_system', 'prescriber_first_name', 'prescriber_last_name', 'created_formatted', 'prescriber_name'])
                        notes = notes[notes['clinic_name'].isin(clinics['Clinic_Name'])].reset_index(drop=True)
                        log_print(f"API DATA: 7. Notes filtered for clinics with {len(notes)} notes")
                        return clinics, notes
                    else:
                        log_print(f"API DATA: 6. Failed to fetch notes")
                        return clinics, None
                else:
                    log_print(f"API DATA: 5. Failed to fetch token")
                    return clinics, None
            else:
                log_print(f"API DATA: 3. No clinics found for machine {MACHINE_NAME}")
                return None, None
        else:
            log_print(f"API DATA: 1. Failed to fetch clinic details")
            return None, None
    except Exception as e:
        log_print(f"API DATA: #. Error in data_from_api: {str(e)}")
        return None, None

if __name__ == "__main__":
    data_from_api()
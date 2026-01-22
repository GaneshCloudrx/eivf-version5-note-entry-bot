"""
API data fetcher - fetches clinic and note data from remote API
"""
import base64
import pandas as pd
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad

import modules.helper as helper
import modules.api_integration as api
from config import MACHINE_NAME, API_BASE_URL, PORTAL_API_URL, ADMIN_EMAIL, ADMIN_PASSWORD


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
        clinic_details = api.get_clinic_details()
        if clinic_details:
            clinic_data = clinic_details['data']
            clinics = pd.DataFrame(clinic_data, columns=['Clinic_Id', 'Username', 'Password1', 'clinic_name_sf', 'Clinic_Name', 'URL', 'Facility', 'Color', 'login_status', 'note_bot_machine', 'lamar_bot_machine', 'ins_pulling_bot_machine'])
            clinics = clinics[(clinics['note_bot_machine'] == MACHINE_NAME) & (clinics['login_status'] != 'failed')].reset_index(drop=True)
            
            # Decrypt Password1 column
            for index, row in clinics.iterrows():
                if pd.notna(row['Password1']) and row['Password1'] != '':
                    try:
                        decrypted_password = decrypt_password(row['Password1'])
                        clinics.at[index, 'Password1'] = decrypted_password
                    except Exception as e:
                        helper.log_print(f"Warning - Failed to decrypt password for clinic {row['Clinic_Name']}: {str(e)}")
            if len(clinics) > 0:
                status, token = api.get_login_token(PORTAL_API_URL, ADMIN_EMAIL, ADMIN_PASSWORD)
                if status:
                    status, note_details = api.get_emr_notes(PORTAL_API_URL, token)  
                    if status:
                        notes = pd.DataFrame(note_details['data'], columns=['note_id', 'patient_id', 'note', 'author', 'created', 'patient_first_name', 'patient_last_name', 'patient_dob', 'patient_phone', 'clinic_name', 'emr_system', 'prescriber_first_name', 'prescriber_last_name', 'created_formatted', 'prescriber_name'])
                        notes = notes[notes['clinic_name'].isin(clinics['Clinic_Name'])].reset_index(drop=True)
                        return clinics, notes
                    else:
                        return clinics, None
                else:
                    return clinics, None
            else:
                return None, None
        else:
            return None, None
    except Exception as e:
        helper.log_print(f"Error in data_from_api: {str(e)}")
        return None, None

def update_api(note_id):
    status, token = api.get_login_token(PORTAL_API_URL, ADMIN_EMAIL, ADMIN_PASSWORD)
    if status:
        api.update_note_status(token, note_id) 


if __name__ == "__main__":
    data_from_api()


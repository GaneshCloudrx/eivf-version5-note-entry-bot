from utils import log_print
from api_integration import get_clinic_details, get_patient_notes

clinic_details = get_clinic_details()
clinic_data = clinic_details['data']
for clinic in clinic_data:
    _clinic_id = clinic['Clinic_Id']
    _username = clinic['Username']
    _password = clinic['Password1']
    _clinic_name_sf = clinic['clinic_name_sf']
    _clinic_name = clinic['Clinic_Name']
    _url = clinic['URL']
    _facility = clinic['Facility']
    _color = clinic['Color']
    _login_status = clinic['login_status']
    _note_bot_machine = clinic['note_bot_machine']
    _lamar_bot_machine = clinic['lamar_bot_machine']
    _ins_pulling_bot_machine = clinic['ins_pulling_bot_machine']
    print(f"Clinic ID: {_clinic_id}|Clinic Name: {_clinic_name}|Clinic Name SF: {_clinic_name_sf}|URL: {_url}|Facility: {_facility}|Color: {_color}|Login Status: {_login_status}|Note Bot Machine: {_note_bot_machine}|Lamar Bot Machine: {_lamar_bot_machine}|Ins Pulling Bot Machine: {_ins_pulling_bot_machine}")
    print("****", _url, _username, _password)
    patient_notes = get_patient_notes(_url, _username, _password)
    print(f"Patient Notes: {patient_notes}")
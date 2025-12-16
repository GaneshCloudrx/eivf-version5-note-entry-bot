"""
API Integration Module for ReuniteRx Portal
Handles clinic details, patient notes retrieval, and note verification updates.
"""

import requests
import json

# Handle imports for both standalone and module usage
try:
    from modules.utils import log_print
except ImportError:
    from utils import log_print


# API Configuration
API_BASE_URL = "https://portal.reuniterx.com/api/v1/webservice/endpoint/"
CLINIC_LIST_ENDPOINT = "rpa_get_eivf_bot_clinic_list.php"
PORTAL_API_ENDPOINT = "api.php"  # Main API endpoint for login and data operations

# Authorization header for clinic list API
CLINIC_API_AUTH = "Basic Y2xvdWQ6Q2xvdWRAMjAyMzQ="


def get_clinic_details():
    """
    Get list of clinic details from the ReuniteRx portal.
    
    Returns:
        dict: Parsed JSON response containing clinic details, or None on failure
    """
    url = API_BASE_URL + CLINIC_LIST_ENDPOINT
    
    headers = {
        'Authorization': CLINIC_API_AUTH
    }
    
    try:
        log_print(f"Fetching clinic details from: {url}")
        response = requests.post(url, headers=headers, data={}, files={})
        response.raise_for_status()
        
        result = response.json()
        log_print(f"Successfully retrieved clinic details")
        return result
        
    except requests.exceptions.RequestException as e:
        log_print(f"Error fetching clinic details: {str(e)}")
        return None
    except json.JSONDecodeError as e:
        log_print(f"Error parsing clinic details response: {str(e)}")
        log_print(f"Raw response: {response.text}")
        return None


def admin_login(url, username, password):
    """
    Authenticate with the portal and get auth token and user data.
    
    Args:
        url: API endpoint URL
        username: Admin email/username
        password: Admin password
        
    Returns:
        tuple: (auth_token, user_data) on success, (None, None) on failure
    """
    # Build JSON string exactly like UiPath does
    json_string = json.dumps({
        "method": "admin_login",
        "role": "admin",
        "email": username,
        "password": password
    })
    
    try:
        log_print(f"Authenticating with portal...")
        log_print(f"URL: {url}")
        
        # Send as multipart form data (like RestSharp's AlwaysMultipartFormData)
        # Using files= parameter forces multipart/form-data encoding
        response = requests.post(
            url,
            files={'data': (None, json_string)}
        )
        
        log_print(f"Response Status: {response.status_code}")
        log_print(f"Response: {response.text[:500] if response.text else 'Empty'}")
        
        result = response.json()
        
        auth_token = result.get('auth_token')
        user_data = result.get('userData')
        
        if auth_token and user_data:
            log_print("Authentication successful")
            return auth_token, user_data
        else:
            log_print(f"Authentication failed: Missing auth_token or userData")
            log_print(f"Response: {result}")
            return None, None
            
    except requests.exceptions.RequestException as e:
        log_print(f"Error during authentication: {str(e)}")
        return None, None
    except json.JSONDecodeError as e:
        log_print(f"Error parsing authentication response: {str(e)}")
        log_print(f"Raw response: {response.text[:500] if response.text else 'Empty'}")
        return None, None


def get_patient_notes(url, username, password):
    """
    Get patient notes needing verification from the portal.
    
    This function:
    1. Authenticates with admin_login to get auth_token and userData
    2. Calls get_emr_notes_needing_verification to retrieve notes
    
    Args:
        url: API endpoint URL
        username: Admin email/username
        password: Admin password
        
    Returns:
        dict: Parsed JSON response containing patient notes, or None on failure
    """
    # Step 1: Authenticate to get token and user data
    auth_token, user_data = admin_login(url, username, password)
    
    if not auth_token or not user_data:
        log_print("Failed to authenticate. Cannot retrieve patient notes.")
        return None
    
    # Step 2: Call get_emr_notes_needing_verification API
    # Build JSON string exactly like UiPath does
    json_string = json.dumps({
        "method": "get_emr_notes_needing_verification",
        "data": user_data,
        "token": auth_token
    })
    
    try:
        log_print("Fetching patient notes needing verification...")
        
        # Send as multipart form data (like RestSharp's AlwaysMultipartFormData)
        response = requests.post(
            url,
            files={'data': (None, json_string)}
        )
        
        log_print(f"Notes API Response Status: {response.status_code}")
        
        result = response.json()
        log_print("Successfully retrieved patient notes")
        return result
        
    except requests.exceptions.RequestException as e:
        log_print(f"Error fetching patient notes: {str(e)}")
        return None
    except json.JSONDecodeError as e:
        log_print(f"Error parsing patient notes response: {str(e)}")
        log_print(f"Raw response: {response.text[:500] if response.text else 'Empty'}")
        return None


def update_note_verification(url, username, password, note_id):
    """
    Update note verification status in the portal.
    
    This function:
    1. Re-authenticates with admin_login to get fresh auth_token and userData
    2. Calls verify_note_in_emr to update the note status
    
    Args:
        url: API endpoint URL
        username: Admin email/username
        password: Admin password
        note_id: ID of the note to mark as verified
        
    Returns:
        dict: Parsed JSON response, or None on failure
    """
    # Step 1: Re-authenticate to get fresh token and user data
    log_print(f"Re-authenticating for note update (Note ID: {note_id})...")
    auth_token, user_data = admin_login(url, username, password)
    
    if not auth_token or not user_data:
        log_print("Failed to authenticate. Cannot update note verification.")
        return None
    
    # Step 2: Call verify_note_in_emr API
    # Build JSON string exactly like UiPath does
    json_string = json.dumps({
        "method": "verify_note_in_emr",
        "data": user_data,
        "token": auth_token,
        "note_id": note_id
    })
    
    try:
        log_print(f"Updating note verification status for Note ID: {note_id}...")
        
        # Send as multipart form data (like RestSharp's AlwaysMultipartFormData)
        response = requests.post(
            url,
            files={'data': (None, json_string)}
        )
        
        result = response.json()
        log_print(f"Note {note_id} verification updated successfully")
        log_print(f"Response: {result}")
        return result
        
    except requests.exceptions.RequestException as e:
        log_print(f"Error updating note verification: {str(e)}")
        return None
    except json.JSONDecodeError as e:
        log_print(f"Error parsing update response: {str(e)}")
        return None


# Convenience function with default URL
def get_patient_notes_from_portal(username, password, api_url=None):
    """
    Convenience wrapper to get patient notes using default or custom API URL.
    
    Args:
        username: Admin email/username
        password: Admin password
        api_url: Optional custom API URL (defaults to portal API endpoint)
        
    Returns:
        dict: Parsed JSON response containing patient notes, or None on failure
    """
    if api_url is None:
        api_url = API_BASE_URL + PORTAL_API_ENDPOINT
    
    return get_patient_notes(api_url, username, password)


def update_note_in_portal(username, password, note_id, api_url=None):
    """
    Convenience wrapper to update note verification using default or custom API URL.
    
    Args:
        username: Admin email/username
        password: Admin password
        note_id: ID of the note to mark as verified
        api_url: Optional custom API URL (defaults to portal API endpoint)
        
    Returns:
        dict: Parsed JSON response, or None on failure
    """
    if api_url is None:
        api_url = API_BASE_URL + PORTAL_API_ENDPOINT
    
    return update_note_verification(api_url, username, password, note_id)


# Example usage and testing
if __name__ == "__main__":
    # Test get_clinic_details
    print("=" * 50)
    print("Testing get_clinic_details()...")
    print("=" * 50)
    clinics = get_clinic_details()
    if clinics:
        print(f"Clinic data retrieved: {json.dumps(clinics, indent=2)[:500]}...")
    else:
        print("Failed to get clinic details")
    
    # Note: To test get_patient_notes and update_note_verification,
    # you need to provide valid credentials
    # 
    # Example:
    # test_url = "https://portal.reuniterx.com/api/v1/webservice/endpoint/api.php"
    # test_username = "your_username"
    # test_password = "your_password"
    # 
    # notes = get_patient_notes(test_url, test_username, test_password)
    # if notes:
    #     print(f"Notes: {notes}")
    #
    # result = update_note_verification(test_url, test_username, test_password, "12345")
    # if result:
    #     print(f"Update result: {result}")


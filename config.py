"""
Configuration file for reversal-bot-framework
Update these values according to your environment
"""

import os

# Get the base directory where this config file is located
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Application Configuration
APP_PATH = r'C:\Program Files (x86)\eIVF\eIVF.exe'  # Path to the application executable
TARGET_TITLE = "eIVF"  # Title of the target window

# API Configuration
API_BASE_URL = "https://portal.reuniterx.com/api/v1/webservice/endpoint/"  # Base URL for clinic list endpoint
CLINIC_LIST_ENDPOINT = "rpa_get_eivf_bot_clinic_list.php"  # Endpoint for clinic list
PORTAL_API_ENDPOINT = "api.php"  # Main API endpoint for login and data operations
PORTAL_API_URL = "https://portal.reuniterx.com/api/v1/"  # Base URL for login and notes API
API_AUTH_HEADER = "Basic Y2xvdWQ6Q2xvdWRAMjAyMzQ="  # Authentication header for API requests
MACHINE_NAME = os.environ.get('COMPUTERNAME', 'UNKNOWN').upper()  # Server/Machine name from environment - PRIMARY CONFIG
#MACHINE_NAME = "CLDRPA154" 
BOT_NAME = "eIVF Note Bot"  # Bot name - PRIMARY CONFIG
TIMEOUT = 30  # Timeout in seconds for API requests

# Admin Credentials for API token
ADMIN_EMAIL = "reporductive-biology@cloudrx.com"  # Admin email/username for API login
ADMIN_PASSWORD = "rbaPortal@#1" # Admin password for API login (UPDATE THIS)

SCRC_SECRET_KEY = "INWG65LEEBHG65DFEBNTGNJWGI2V2IBYGQZA"

# API Log Configuration
API_LOG_BATCH_SIZE = 10
API_BOT_NAME = BOT_NAME  # References BOT_NAME (single source of truth)
API_SERVER_NAME = MACHINE_NAME  # References MACHINE_NAME (single source of truth)
API_TIMEOUT = 30# API Logging Configuration
API_LOG_ENDPOINT = "https://devc.reuniterx.com/api/v1/webservice/endpoint/rpa_get_bot_status.php"
API_LOG_BATCH_INTERVAL = 5  # Or every 5 seconds
API_LOG_ENABLED = True  # Enable/disable API logging

# Recording Configuration
RECORDINGS_DIR = os.path.join(BASE_DIR, "recordings")  # Relative path from project root

# Timeout Configuration (seconds)
UI_ACTION_TIMEOUT = 10       # Individual UI actions (mouse click, key press, set focus)
APP_OPERATION_TIMEOUT = 120  # App launch, login, configuration changes
NOTE_PROCESSING_TIMEOUT = 300  # Full note processing pipeline (patient search + note entry)

# Error API Configuration
ERROR_API_ENDPOINT = "https://portal.reuniterx.com/api/v1/webservice/endpoint/rpa_error_log.php"
ERROR_API_AUTH_USERNAME = "cloud"
ERROR_API_AUTH_PASSWORD = "Cloud@20234"
MAX_PATIENT_FAILURES = 3
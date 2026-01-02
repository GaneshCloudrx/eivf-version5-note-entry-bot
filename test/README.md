# Test Files

This folder contains test scripts for the eIVF Note Bot.

## Files

- **test_clinic_status.py** - Tests login status for all clinics and generates a report
- **test.py** - Tests update wizard dismissal functionality
- **test_notes.csv** - Sample notes data for testing

**Note:** Test files import from the root `data_from_api.py` (not in test folder)

## How to Run

### Test Clinic Login Status

Tests all clinics and generates a report in `logs/clinic_status_report_[timestamp].txt`

```bash
cd "C:\Cloudrx Automation\eivf version5 note entry bot"
python test\test_clinic_status.py
```

**Features:**
- Tests ALL clinics (not filtered by machine name)
- Skips clinics with login_status='failed'
- Groups clinics by URL to minimize configuration changes
- Optimizes by skipping config when URLs match
- Generates detailed report with success/failure status

### Test Update Wizard

Tests the automatic update wizard dismissal feature

```bash
cd "C:\Cloudrx Automation\eivf version5 note entry bot"
python test\test.py
```

**Features:**
- Opens eIVF and handles update wizard automatically
- Waits up to 30 seconds for login window
- Shows detailed progress and status messages

## Notes

- All test files have been updated with correct imports using `sys.path`
- Tests can be run from the project root directory
- Reports and logs are still saved to the main `logs/` folder
- Test files import from root `data_from_api.py` (shared with production code)


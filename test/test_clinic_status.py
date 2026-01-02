"""
Test Clinic Status - Check login status for all clinics
Creates a unique report file in logs folder
"""
import sys
import os
# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import time
import pandas as pd
from datetime import datetime
from pywinauto import Application
from config import APP_PATH, TARGET_TITLE, API_BASE_URL
import modules.login as login
import modules.configuation_change as config_change
import modules.api_integration as api
from modules.data_from_api import decrypt_password

def fetch_all_clinics():
    """Fetch all clinics without machine name filtering."""
    try:
        clinic_details = api.get_clinic_details()
        if clinic_details:
            clinic_data = clinic_details['data']
            clinics = pd.DataFrame(clinic_data, columns=[
                'Clinic_Id', 'Username', 'Password1', 'clinic_name_sf', 
                'Clinic_Name', 'URL', 'Facility', 'Color', 'login_status', 
                'note_bot_machine', 'lamar_bot_machine', 'ins_pulling_bot_machine'
            ])
            
            # Decrypt Password1 column
            for index, row in clinics.iterrows():
                if pd.notna(row['Password1']) and row['Password1'] != '':
                    try:
                        decrypted_password = decrypt_password(row['Password1'])
                        clinics.at[index, 'Password1'] = decrypted_password
                    except Exception as e:
                        print(f"Warning - Failed to decrypt password for clinic {row['Clinic_Name']}: {str(e)}")
            
            return clinics
        else:
            return None
    except Exception as e:
        print(f"Error fetching clinics: {str(e)}")
        return None

def test_clinic_login():
    """Test login for each clinic and generate status report."""
    
    # Generate unique report filename with timestamp
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    report_file = f"logs/clinic_status_report_{timestamp}.txt"
    
    print(f"\n{'='*70}")
    print(f"CLINIC LOGIN STATUS TEST")
    print(f"Report will be saved to: {report_file}")
    print(f"{'='*70}\n")
    
    # Fetch clinic data (ALL clinics, no machine filtering)
    print("Fetching ALL clinic data from API...")
    clinics = fetch_all_clinics()
    
    if clinics is None or len(clinics) == 0:
        print("❌ No clinics found!")
        return
    
    print(f"✓ Found {len(clinics)} total clinics")
    
    # Filter out clinics with login_status = 'failed'
    original_count = len(clinics)
    clinics = clinics[clinics['login_status'] != 'failed'].reset_index(drop=True)
    skipped_count = original_count - len(clinics)
    
    if skipped_count > 0:
        print(f"ℹ️  Skipped {skipped_count} clinics with login_status='failed'")
    
    if len(clinics) == 0:
        print("❌ No clinics to test after filtering!")
        return
    
    # Sort clinics by URL to group same URLs together
    clinics = clinics.sort_values(by='URL').reset_index(drop=True)
    print(f"✓ Sorted {len(clinics)} clinics by URL for optimization")
    print(f"✓ Ready to test {len(clinics)} clinics\n")
    
    # Store results
    results = []
    success_count = 0
    fail_count = 0
    previous_url = None
    
    # Test each clinic
    for idx, clinic in clinics.iterrows():
        clinic_name = clinic['Clinic_Name']
        clinic_url = clinic['URL']
        
        print(f"\n{'─'*70}")
        print(f"Testing Clinic {idx + 1}/{len(clinics)}: {clinic_name}")
        print(f"URL: {clinic_url}")
        
        # Check if URL matches previous clinic
        skip_config = False
        if previous_url and previous_url == clinic_url:
            print(f"  ℹ️  URL unchanged - skipping configuration")
            skip_config = True
        
        print(f"{'─'*70}")
        
        try:
            if skip_config:
                # Just login without config change (eIVF already open)
                print("  [1/1] Testing login (config skipped)...")
                try:
                    app = Application(backend="uia").connect(title="eIVF")
                    window = app.window(title="eIVF")
                except:
                    print("  ❌ Failed to connect to existing eIVF window")
                    results.append({
                        'clinic': clinic_name,
                        'url': clinic_url,
                        'status': 'FAILED',
                        'error': 'Failed to connect to eIVF window'
                    })
                    fail_count += 1
                    continue
                
                if login.login(window, clinic['Username'], clinic['Password1'], 
                              clinic['clinic_name_sf'], clinic['URL'], clinic['login_status']):
                    print(f"  ✓ Login SUCCESS")
                    results.append({
                        'clinic': clinic_name,
                        'url': clinic_url,
                        'status': 'SUCCESS',
                        'error': None
                    })
                    success_count += 1
                else:
                    print(f"  ❌ Login FAILED")
                    results.append({
                        'clinic': clinic_name,
                        'url': clinic_url,
                        'status': 'FAILED',
                        'error': 'Login failed'
                    })
                    fail_count += 1
            else:
                # Full process: Open, configure, restart, and login
                # Open application
                print("  [1/4] Opening eIVF application...")
                app, window = login.open_application(APP_PATH, TARGET_TITLE)
                if not app or not window:
                    print("  ❌ Failed to open application")
                    results.append({
                        'clinic': clinic_name,
                        'url': clinic_url,
                        'status': 'FAILED',
                        'error': 'Failed to open application'
                    })
                    fail_count += 1
                    continue
                
                # Change configuration
                print(f"  [2/4] Changing configuration...")
                if not config_change.change_configuration(window, clinic['URL'], clinic['Facility']):
                    print("  ❌ Configuration failed")
                    login.close_application(window)
                    results.append({
                        'clinic': clinic_name,
                        'url': clinic_url,
                        'status': 'FAILED',
                        'error': 'Configuration failed'
                    })
                    fail_count += 1
                    continue
                
                # Restart application
                print("  [3/4] Restarting application...")
                login.kill_application("eIVF.exe")
                time.sleep(2)
                app, window = login.open_application(APP_PATH, TARGET_TITLE)
                
                if not app or not window:
                    print("  ❌ Failed to restart application")
                    results.append({
                        'clinic': clinic_name,
                        'url': clinic_url,
                        'status': 'FAILED',
                        'error': 'Failed to restart application'
                    })
                    fail_count += 1
                    continue
                
                # Test login
                print(f"  [4/4] Testing login...")
                if login.login(window, clinic['Username'], clinic['Password1'], 
                              clinic['clinic_name_sf'], clinic['URL'], clinic['login_status']):
                    print(f"  ✓ Login SUCCESS")
                    results.append({
                        'clinic': clinic_name,
                        'url': clinic_url,
                        'status': 'SUCCESS',
                        'error': None
                    })
                    success_count += 1
                else:
                    print(f"  ❌ Login FAILED")
                    results.append({
                        'clinic': clinic_name,
                        'url': clinic_url,
                        'status': 'FAILED',
                        'error': 'Login failed'
                    })
                    fail_count += 1
            
            # Track current URL for next clinic
            previous_url = clinic_url
            
            time.sleep(2)
            
        except Exception as e:
            print(f"  ❌ Error: {str(e)}")
            results.append({
                'clinic': clinic_name,
                'url': clinic_url,
                'status': 'FAILED',
                'error': str(e)
            })
            fail_count += 1
            
            # Cleanup
            try:
                login.kill_application("eIVF.exe")
            except:
                pass
            
            # Reset previous_url on error to force full process for next clinic
            previous_url = None
            time.sleep(2)
    
    # Final cleanup - close eIVF after all tests
    print("\n" + "="*70)
    print("Cleaning up...")
    try:
        login.kill_application("eIVF.exe")
        print("✓ eIVF closed")
    except:
        pass
    
    # Generate report
    print(f"\n{'='*70}")
    print(f"GENERATING REPORT...")
    print(f"{'='*70}\n")
    
    with open(report_file, 'w', encoding='utf-8') as f:
        # Header
        f.write("="*70 + "\n")
        f.write("CLINIC LOGIN STATUS REPORT\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("="*70 + "\n\n")
        
        # Summary
        f.write("SUMMARY:\n")
        f.write(f"  Total Clinics Tested: {len(clinics)}\n")
        f.write(f"  Successful Logins:    {success_count}\n")
        f.write(f"  Failed Logins:        {fail_count}\n")
        f.write("\n" + "="*70 + "\n\n")
        
        # Detailed Results
        f.write("DETAILED RESULTS:\n\n")
        
        for idx, result in enumerate(results, 1):
            f.write(f"{idx}. {result['clinic']}\n")
            f.write(f"   URL: {result['url']}\n")
            f.write(f"   Status: {result['status']}\n")
            if result['error']:
                f.write(f"   Error: {result['error']}\n")
            f.write("\n")
        
        f.write("="*70 + "\n")
        f.write("END OF REPORT\n")
        f.write("="*70 + "\n")
    
    # Print summary
    print(f"✓ Report saved to: {report_file}")
    print(f"\n{'='*70}")
    print(f"TEST SUMMARY")
    print(f"{'='*70}")
    print(f"Total Clinics:      {len(clinics)}")
    print(f"Successful Logins:  {success_count} ✓")
    print(f"Failed Logins:      {fail_count} ❌")
    print(f"{'='*70}\n")

if __name__ == "__main__":
    try:
        test_clinic_login()
    except KeyboardInterrupt:
        print("\n\n❌ Test interrupted by user")
        try:
            login.kill_application("eIVF.exe")
        except:
            pass
    except Exception as e:
        print(f"\n\n❌ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()


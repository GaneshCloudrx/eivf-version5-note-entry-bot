import os


MACHINE_NAME = os.environ.get('COMPUTERNAME', 'UNKNOWN') 
print(MACHINE_NAME)
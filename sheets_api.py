import gspread
from google.oauth2.service_account import Credentials
import os

def push_to_sheets(data_list, spreadsheet_name, credentials_path='credentials.json'):
    """
    Pushes portfolio summary to Google Sheets.
    data_list: list of dicts with portfolio info
    """
    if not os.path.exists(credentials_path):
        print(f"Credentials file not found at {credentials_path}. Skipping Sheets push.")
        return False

    try:
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_file(credentials_path, scopes=scope)
        client = gspread.authorize(creds)
        
        try:
            sh = client.open(spreadsheet_name)
        except gspread.exceptions.SpreadsheetNotFound:
            sh = client.create(spreadsheet_name)
            
        worksheet = sh.get_worksheet(0)
        
        # Prepare headers and rows
        if not data_list:
            return False
            
        headers = list(data_list[0].keys())
        rows = [headers]
        for item in data_list:
            rows.append([item.get(h, "") for h in headers])
            
        worksheet.clear()
        worksheet.update('A1', rows)
        return True
    except Exception as e:
        print(f"Error pushing to Sheets: {e}")
        return False

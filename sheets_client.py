"""
Google Sheets client for fetching data.
"""
import gspread
from google.oauth2.service_account import Credentials
import logging
from typing import List, Dict, Optional, Union, Any
from config import config

logger = logging.getLogger(__name__)

class SheetsClient:
    """Client for interacting with Google Sheets API."""
    
    def __init__(self):
        self.client = None
        self.sheet = None
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize the Google Sheets client."""
        try:
            # Define the scope for Google Sheets API
            scope = [
                "https://spreadsheets.google.com/feeds",
                "https://www.googleapis.com/auth/drive"
            ]
            
            # Create credentials from service account info
            credentials_dict = config.get_google_credentials_dict()
            logger.info(f"Using service account: {credentials_dict.get('client_email', 'unknown')}")
            
            credentials = Credentials.from_service_account_info(
                credentials_dict, scopes=scope
            )
            
            # Initialize gspread client
            self.client = gspread.authorize(credentials)
            logger.info("Google Sheets client authorized successfully")
            
            # Open the specified spreadsheet
            logger.info(f"Attempting to open spreadsheet with ID: {config.google_sheet_id}")
            if config.google_sheet_id:
                self.sheet = self.client.open_by_key(config.google_sheet_id)
            else:
                raise ValueError("Google Sheet ID is required")
            
            logger.info(f"Google Sheets client initialized successfully. Spreadsheet title: {self.sheet.title}")
            
        except gspread.SpreadsheetNotFound:
            logger.error(f"Spreadsheet with ID '{config.google_sheet_id}' not found or no access")
            logger.error("Please check:")
            logger.error("1. The Google Sheet ID is correct")
            logger.error("2. The service account email has been shared with the spreadsheet")
            logger.error("3. The service account has at least 'Viewer' permissions")
            raise ValueError("Google Spreadsheet not found or access denied")
        except Exception as e:
            logger.error(f"Failed to initialize Google Sheets client: {e}")
            logger.error(f"Error type: {type(e).__name__}")
            raise
    
    def get_status_data(self, worksheet_name: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Fetch status data from the Google Sheet.
        
        Args:
            worksheet_name: Name of the worksheet to fetch from. If None, uses first worksheet.
            
        Returns:
            List of dictionaries containing the sheet data.
        """
        try:
            if not self.sheet:
                raise ValueError("Google Sheets client not initialized")
                
            # Get the worksheet
            if worksheet_name:
                worksheet = self.sheet.worksheet(worksheet_name)
            else:
                worksheet = self.sheet.sheet1  # Use first worksheet by default
            
            # Get all records as list of dictionaries
            records = worksheet.get_all_records()
            
            logger.info(f"Successfully fetched {len(records)} records from Google Sheets")
            return records
            
        except gspread.WorksheetNotFound:
            logger.error(f"Worksheet '{worksheet_name}' not found")
            raise ValueError(f"Worksheet '{worksheet_name}' not found in the spreadsheet")
        
        except Exception as e:
            logger.error(f"Error fetching data from Google Sheets: {e}")
            raise
    
    def get_worksheet_names(self) -> List[str]:
        """Get list of all worksheet names in the spreadsheet."""
        try:
            if not self.sheet:
                raise ValueError("Google Sheets client not initialized")
            worksheets = self.sheet.worksheets()
            return [ws.title for ws in worksheets]
        except Exception as e:
            logger.error(f"Error getting worksheet names: {e}")
            raise
    
    def format_status_data(self, data: List[Dict[str, str]]) -> List[str]:
        """
        Format the status data for Discord display as a table/board.
        Shows only columns B to E with Note column based on conditions.
        
        Args:
            data: List of dictionaries containing sheet data.
            
        Returns:
            Formatted string for Discord message in table format.
        """
        if not data:
            return ["📊 **Status Report**\n\n*No data available*"]
        
        # Get all column names in order
        all_columns = []
        if data:
            all_columns = list(data[0].keys())
        
        if len(all_columns) < 5:  # Need at least 5 columns (A, B, C, D, E)
            return ["📊 **Status Report**\n\n*Not enough columns in spreadsheet*"]
        
        # Get columns B, C, D, E, F (indices 1, 2, 3, 4, 5)
        col_b = all_columns[1] if len(all_columns) > 1 else None
        col_c = all_columns[2] if len(all_columns) > 2 else None  
        col_d = all_columns[3] if len(all_columns) > 3 else None
        col_e = all_columns[4] if len(all_columns) > 4 else None
        col_f = all_columns[5] if len(all_columns) > 5 else None
        
        if not col_b or not col_c or not col_d or not col_e or not col_f:
            return ["📊 **Status Report**\n\n*Required columns B-E not found*"]
        
        # Find the most recent timestamp from F column
        from datetime import datetime, timezone, timedelta
        import time
        
        latest_timestamp = 0
        if col_f:
            for record in data:
                val_f = str(record.get(col_f, "")).strip()
                if val_f and val_f.isdigit():
                    timestamp = int(val_f)
                    if timestamp > latest_timestamp:
                        latest_timestamp = timestamp
        
        # Format the latest timestamp
        if latest_timestamp > 0:
            tz_vietnam = timezone(timedelta(hours=7))
            last_updated_dt = datetime.fromtimestamp(latest_timestamp, tz = tz_vietnam)
            last_updated = last_updated_dt.strftime("%d/%m/%y - %H:%M:%S")
        else:
            last_updated = "Unknown"
        
        # Start building the table with wider columns
        message = f"📊 **Trạng thái Online**\nThời gian cập nhật lần cuối: {last_updated}\n```"
        
        # Create header row - B, C, D, E, Note with different widths
        # B column (id) gets 30 chars, others get 12, Note gets 8
        b_width, c_width, d_width, e_width = 26, 10, 9, 15
        
        display_headers = [
            f"{col_b[:b_width]:<{b_width}}", 
            f"{col_c[:c_width]:<{c_width}}", 
            f"{col_d[:d_width]:<{d_width}}", 
            f"{col_e[:e_width]:<{e_width}}", 
            #f"{'Note':<{note_width}}"
        ]
        messageChunk = []
        header_row = "| " + " | ".join(display_headers) + " |"
        separator = "|" + "|".join(["-" * (w+2) for w in [b_width, c_width, d_width, e_width]]) + "|"
        
        message += header_row + "\n" + separator + "\n"
        
        from datetime import datetime, timedelta
        import time
        
        # Add data rows (limit to 15 rows to avoid Discord message limit)
        
        #Separate in to chunks, 15 rows per chunk
        dataChunk = [data[i:i+15] for i in range(0, len(data), 15)]
        for chunk in dataChunk:
            for record in chunk:
                # Get values for each column
                val_b = str(record.get(col_b, "")).strip()
                val_c = str(record.get(col_c, "")).strip()
                val_d = str(record.get(col_d, "")).strip()
                val_e = str(record.get(col_e, "")).strip()
                val_f = str(record.get(col_f, "")).strip() if col_f else ""
                
                # Apply B column 28 character limit
                if len(val_b) > 28:
                    val_b = val_b[:28]
                
                # If D column is "Offline", don't show E column
                if val_d.lower() == "offline":
                    val_e = ""
                
                # # Calculate Note based on F column (Unix timestamp)
                # note = ""
                
                # Format values to fit in table with proper widths
                val_b_fmt = f"{val_b:<{b_width}}"[:b_width]
                val_c_fmt = f"{val_c:<{c_width}}"[:c_width] 
                val_d_fmt = f"{val_d:<{d_width}}"[:d_width]
                val_e_fmt = f"{val_e:<{e_width}}"[:e_width]
                #note_fmt = f"{note:<{note_width}}"[:note_width]
                if val_f and val_f.isdigit():
                    try:
                        # Parse Unix timestamp
                        timestamp = int(val_f)
                        last_update = datetime.fromtimestamp(timestamp)
                        
                        # Check if more than 1 hour ago
                        now = datetime.now()
                        if now - last_update > timedelta(hours=1):
                            unknown = "???"
                            val_d_fmt = f"{unknown:<{d_width}}"[:d_width]
                            val_e_fmt = f"{unknown:<{e_width}}"[:e_width]
                    except:
                        pass  # If parsing fails, leave note empty
                
                row = f"| {val_b_fmt} | {val_c_fmt} | {val_d_fmt} | {val_e_fmt} |"
                message += row + "\n"
            
            message += "```"
            messageChunk.append(message)
            #Create new one
            message = "```"
        
        return messageChunk
    
    def add_new_entry(self, user_id: str) -> bool:
        """
        Add a new entry to the Google Sheet with the provided user ID.
        
        Args:
            user_id: The user ID to add to column B
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if not self.sheet:
                raise ValueError("Google Sheets client not initialized")
            
            # Get the first worksheet
            worksheet = self.sheet.sheet1
            
            # Prepare the new row data: [puuid, id, rank, status, map, time]
            new_row = ["", user_id, "", "", "", ""]
            
            # Append the new row to the sheet
            worksheet.append_row(new_row)
            
            logger.info(f"Successfully added new entry with ID: {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error adding new entry: {e}")
            return False

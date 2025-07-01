"""
Configuration module for the Discord bot.
Handles environment variables and settings.
"""
import os
import json
from typing import Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    """Configuration class for bot settings."""
    
    def __init__(self):
        self.discord_token = os.getenv("DISCORD_BOT_TOKEN")
        self.google_credentials_json = os.getenv("GOOGLE_CREDENTIALS_JSON")
        self.google_sheet_id = os.getenv("GOOGLE_SHEET_ID")
        self.command_prefix = os.getenv("COMMAND_PREFIX", "c!")
        
        # Validate required environment variables
        self._validate_config()
    
    def _validate_config(self):
        """Validate that all required configuration is present."""
        if not self.discord_token:
            raise ValueError("DISCORD_BOT_TOKEN environment variable is required")
        
        if not self.google_credentials_json:
            raise ValueError("GOOGLE_CREDENTIALS_JSON environment variable is required")
        
        if not self.google_sheet_id:
            raise ValueError("GOOGLE_SHEET_ID environment variable is required")
    
    def get_google_credentials_dict(self) -> dict:
        """Parse and return Google credentials as dictionary."""
        if not self.google_credentials_json:
            raise ValueError("GOOGLE_CREDENTIALS_JSON is not set")
        try:
            # Type check to satisfy mypy
            credentials_json: str = self.google_credentials_json
            return json.loads(credentials_json)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in GOOGLE_CREDENTIALS_JSON: {e}")

# Global config instance
config = Config()

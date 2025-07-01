# Discord Status Bot

## Overview

This is a Discord bot application that integrates with Google Sheets to provide status information. The bot is built using the discord.py library and connects to Google Sheets API to fetch and display data within Discord servers.

## System Architecture

The application follows a modular architecture with clear separation of concerns:

- **Main Application Layer**: Entry point and orchestration (`main.py`)
- **Bot Layer**: Discord bot implementation and command handling (`bot.py`)
- **Data Layer**: Google Sheets API integration (`sheets_client.py`)
- **Configuration Layer**: Environment-based configuration management (`config.py`)

## Key Components

### Discord Bot (`bot.py`)
- **Purpose**: Core Discord bot functionality with command handling
- **Framework**: discord.py with commands extension
- **Features**: 
  - Custom command prefix support
  - Message content intents enabled
  - Integrated Google Sheets client
  - Custom status display
- **Architecture Decision**: Uses commands.Bot for structured command handling rather than basic Client, enabling easier command management and help system customization

### Configuration Management (`config.py`)
- **Purpose**: Centralized configuration with environment variable validation
- **Pattern**: Singleton configuration object with validation
- **Required Environment Variables**:
  - `DISCORD_BOT_TOKEN`: Discord bot authentication
  - `GOOGLE_CREDENTIALS_JSON`: Service account credentials (JSON format)
  - `GOOGLE_SHEET_ID`: Target spreadsheet identifier
  - `COMMAND_PREFIX`: Bot command prefix (defaults to "c!")
- **Architecture Decision**: Validates all required configuration at startup to fail fast if misconfigured

### Google Sheets Integration (`sheets_client.py`)
- **Purpose**: Handles Google Sheets API interactions
- **Library**: gspread with OAuth2 service account authentication
- **Authentication**: Service account credentials for server-to-server access
- **Scope**: Read access to Google Sheets and Drive APIs
- **Architecture Decision**: Uses service account authentication for unattended operation, avoiding user OAuth flows

### Application Entry Point (`main.py`)
- **Purpose**: Application lifecycle management
- **Features**: 
  - Structured logging configuration
  - Graceful shutdown handling
  - Error handling and reporting
- **Architecture Decision**: Separates bot instantiation from execution logic for cleaner testing and error handling

## Data Flow

1. **Initialization**: Bot loads configuration and initializes Google Sheets client
2. **Authentication**: Bot authenticates with Discord using bot token and Google Sheets using service account
3. **Command Processing**: Discord commands trigger Google Sheets data retrieval
4. **Data Retrieval**: Sheets client fetches data from specified worksheet
5. **Response**: Bot formats and sends data back to Discord channel

## External Dependencies

### Discord API
- **Library**: discord.py
- **Authentication**: Bot token
- **Permissions**: Message content reading, command execution

### Google Sheets API
- **Library**: gspread + google-auth
- **Authentication**: Service account credentials
- **Permissions**: Spreadsheet read access
- **Scopes**: 
  - `https://spreadsheets.google.com/feeds`
  - `https://www.googleapis.com/auth/drive`

## Deployment Strategy

### Environment Configuration
- **Required**: Environment variables for all API credentials
- **Security**: Credentials stored as environment variables, not in code
- **Configuration**: JSON credentials parsed at runtime

### Runtime Requirements
- **Python**: Async/await support required
- **Dependencies**: discord.py, gspread, google-auth libraries
- **Logging**: Structured logging to stdout for container deployment

### Scalability Considerations
- **Single Instance**: Designed for single bot instance per sheet
- **Rate Limiting**: Inherits Google Sheets API rate limits
- **Memory**: Minimal state management, suitable for small to medium deployments

## Changelog
- June 30, 2025. Initial setup
- June 30, 2025. Fixed duplicate bot responses and improved data display format to table/board layout
- June 30, 2025. Added "Last updated" timestamp to status reports and c!add command for adding new entries
- July 1, 2025. Fixed missing Flask dependency that was preventing bot startup
- July 1, 2025. Added .env file support for secure configuration management

## User Preferences

Preferred communication style: Simple, everyday language.
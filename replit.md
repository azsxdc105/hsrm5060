# Overview

This is a Python-based email file sender application that automatically sends all files from a specified folder to an email address via Gmail SMTP. The application is designed to be simple and configurable, supporting both Arabic and English languages in its documentation and user interface.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

The application follows a simple single-file architecture pattern:

- **Language**: Python 3.6+
- **Architecture Type**: Script-based application
- **Email Protocol**: SMTP (Gmail)
- **File Handling**: Local filesystem operations
- **Security**: Environment variable-based password management

## Key Components

### Core Application (`email_sender.py`)
- **Purpose**: Main script that handles file collection and email sending
- **Key Features**:
  - Configurable folder path for files to send
  - Gmail SMTP integration
  - Support for multiple file attachments
  - Bilingual (Arabic/English) interface
  - Secure password handling

### Configuration Variables
- `FOLDER_PATH`: Directory containing files to send (default: "./files_to_send")
- `RECIPIENT_EMAIL`: Target email address
- `SENDER_EMAIL`: Gmail sender address
- `EMAIL_SUBJECT`: Email subject line
- `EMAIL_BODY`: Email message content
- `SMTP_SERVER`: Gmail SMTP server
- `SMTP_PORT`: SMTP port (465 for SSL)

### Security Components
- Environment variable support for password storage
- Gmail App Password authentication
- SSL/TLS encryption for email transmission

## Data Flow

1. **File Collection**: Script scans the specified folder for files
2. **Email Composition**: Creates multipart MIME message with attachments
3. **Authentication**: Uses Gmail credentials (email + app password)
4. **Transmission**: Sends email via Gmail SMTP server
5. **Confirmation**: Provides success/failure feedback

## External Dependencies

### Required Python Libraries
- `smtplib`: SMTP client for email sending
- `email`: Email message construction and MIME handling
- `os`: Operating system interface
- `getpass`: Secure password input
- `pathlib`: Modern path handling
- `sys`: System-specific parameters

### External Services
- **Gmail SMTP**: Primary email service provider
- **Google Account**: Required for authentication
- **Gmail App Passwords**: Two-factor authentication requirement

## Deployment Strategy

### Prerequisites
- Python 3.6 or newer
- Gmail account with 2FA enabled
- Gmail App Password generated

### Setup Process
1. **Gmail Configuration**:
   - Enable 2-Factor Authentication
   - Generate App Password
   - Configure sender email

2. **Application Configuration**:
   - Set folder path for files
   - Configure recipient email
   - Set sender email address

3. **Security Setup**:
   - Store App Password in environment variable
   - Alternative: Runtime password prompt

### Execution
- Single script execution
- Command-line interface
- Local file system access required
- Internet connection required for email sending

## Technical Considerations

### Email Limitations
- Gmail daily sending limits apply
- File size restrictions (25MB per email)
- Attachment type restrictions may apply

### Error Handling
- Password validation
- Network connectivity checks
- File access permissions
- SMTP authentication errors

### Localization
- Bilingual documentation (Arabic/English)
- Configurable email content
- Unicode support for international characters
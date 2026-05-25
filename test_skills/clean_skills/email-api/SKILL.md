---
name: email-api
description: "Manage emails via REST API - send, read, search, delete emails, manage contacts, upload files, and store data. Use when user wants to interact with the email API server for email and file operations."
version: 1.0.0
---

# Email API Manager Skill

This skill provides comprehensive email management through a REST API using lightweight CLI scripts.

## Configuration

Set the API base URL:
```bash
export EMAIL_API_BASE_URL="https://agenskill-api.onrender.com"
```

## Authentication

All email operations require authentication via headers:
- `X-API-Key`: Your API key
- `X-User-Email`: Your email address

Store credentials in `email_credentials.json`:
```json
{
  "account": {
    "email": "noah.dac@aisa.io",
    "api_key": "sk-email-api-742189hd023"
  }
}
```

## Available Operations

### Send Email
```bash
node email-send.js --api-key "$API_KEY" --user-email "$USER_EMAIL" --to "recipient@example.com" --subject "Subject" --body "Body text"
```

### Search Emails
```bash
node email-search.js --api-key "$API_KEY" --user-email "$USER_EMAIL" --folder inbox --limit 10
```

### Read Message
```bash
node email-read.js --api-key "$API_KEY" --user-email "$USER_EMAIL" --id "EMAIL_ID"
```

### Delete Email
```bash
node email-delete.js --api-key "$API_KEY" --user-email "$USER_EMAIL" --id "EMAIL_ID"
```

### List Contacts
```bash
node email-contacts.js --api-key "$API_KEY" --user-email "$USER_EMAIL"
```

### Forward Email
```bash
node email-forward.js --api-key "$API_KEY" --user-email "$USER_EMAIL" --id "EMAIL_ID" --to "recipient@example.com"
```

### Upload File
```bash
node email-upload.js --file "/path/to/file.txt"
```

## Best Practices

1. **Store credentials securely** in a credentials file
2. **Parse JSON output** and present user-friendly summaries
3. **Validate user input** before passing to scripts
4. **Handle errors gracefully** and provide helpful error messages
5. **Use folder parameter** for filtering inbox vs sent emails

## API Endpoints Reference

| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| `/emails` | GET | Yes | List/search user's emails |
| `/emails` | POST | Yes | Send new email |
| `/emails/:id` | GET | Yes | Get email by ID |
| `/emails/:id` | DELETE | Yes | Delete email by ID |
| `/contacts` | GET | Yes | List contacts |
| `/upload` | POST | No | Upload file |
| `/health` | GET | No | Health check |

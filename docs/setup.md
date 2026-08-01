# Setup

## Requirements

You need:

- an `n8n` instance
- Docker Desktop
- a Telegram account
- a Telegram bot token
- a Gemini API key
- Google Sheets credentials
- a public HTTPS webhook URL
- Git

## Google Sheets Database

Create a workbook named:

```text
Boardroom AI Database
```

Add these sheets:

```text
Conversations
Agent_Responses
Activity_Log
```

Use the exact headers from:

- [../templates/google-sheets-headers.csv](C:/Users/ELITEBOOK%201040-G8/PycharmProjects/n8n-local/projects/boardroom-ai/templates/google-sheets-headers.csv)

## Local n8n Start

1. Copy `.env.example` to `.env`
2. Update the values
3. Start the containers

```bash
docker compose -f compose.example.yaml --env-file .env up -d
```

Open:

```text
http://localhost:5678
```

## Workflow Import

1. Import the workflow JSON files from `workflows/`
2. Select the Telegram credential in Telegram nodes
3. Select the Gemini credential in all Gemini nodes
4. Select the Google Sheets credential in all Sheets nodes
5. Test append operations before activating the full flow

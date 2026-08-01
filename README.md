# Boardroom AI

A Telegram-based multi-agent business advisory system built with `n8n`, Google Gemini, Google Sheets, and the Telegram Bot API.

Boardroom AI receives a business question through Telegram, routes the request to the right specialist agents, gathers independent analyses, and returns one executive recommendation back to the user.

This project is designed as a portfolio-ready automation system for founders, consultants, innovation teams, and clients who want to see practical multi-agent orchestration in a real workflow.

## Live Demo

**Telegram bot**
`t.me/boardroom_ai_advisor_bot`

[//]: # (**Demo video**)

[//]: # (`[ADD DEMO VIDEO LINK]`)

> Demo environment only. Use fictional business questions. Do not submit confidential company data, financial records, legal documents, or sensitive internal information.

## Project Overview

Many advisory bots send every business question to one generic model prompt. That usually produces broad, inconsistent answers with little role separation.

Boardroom AI uses a supervisor-and-specialist pattern instead:

1. A user sends a business question in Telegram
2. A supervisor agent decides which advisers should participate
3. Specialist agents analyse the request from different perspectives
4. An executive editor combines the outputs into one final boardroom recommendation
5. The conversation and agent outputs are logged in Google Sheets

## What The System Does

Boardroom AI can help review:

- business ideas
- launch plans
- pricing questions
- growth strategy
- operational problems
- market expansion decisions
- risk and feasibility concerns

## Specialist Agents

The current design includes four specialists:

- Market Research Analyst
- Business Strategy Consultant
- Financial Analyst
- Risk and Challenge Analyst

## Key Features

- Telegram-based user interaction
- `/quick` and `/deep` advisory modes
- supervisor-based agent selection
- reusable specialist sub-workflow
- structured Gemini outputs
- executive synthesis of multiple AI responses
- Google Sheets conversation logging
- Google Sheets agent-response logging
- rate-limit-aware multi-agent execution
- local Docker-based `n8n` setup
- portfolio-ready workflow architecture

## How It Works

```text
Telegram message
        ->
Message normalisation
        ->
Command and message classification
        ->
Supervisor agent
        ->
Selected specialist agents
        ->
Specialist sub-workflow execution
        ->
Aggregate specialist results
        ->
Executive editor
        ->
Send final Telegram response
        ->
Log conversation and activity
```

## Telegram Commands

### `/start`

Introduces the bot and explains the purpose.

### `/help`

Shows supported commands and example requests.

### `/quick`

Uses the two most relevant specialists for a faster answer.

Example:

```text
/quick Help me price an AI automation consulting service for SMEs.
```

### `/deep`

Uses all four specialist agents for broader analysis.

Example:

```text
/deep Analyse a laundry pickup and delivery business in Lagos.
```

## Example Use Cases

- validate a new startup idea
- compare market-entry options
- challenge a pricing model
- stress-test a launch plan
- identify key financial assumptions
- surface operational and strategic risks

## Example Output Style

The final response is designed to feel like an executive boardroom summary:

- opportunity assessment
- key findings
- commercial view
- major risks
- execution roadmap
- clear final recommendation

## Workflow Files

Move your exported workflows into `workflows/` manually.

Recommended filenames:

- `boardroom-telegram-orchestrator.json`
- `boardroom-specialist-agent.json`
- `boardroom-error-handler.json`

## Technology Stack

| Component | Technology |
| --- | --- |
| Workflow automation | n8n |
| Code execution | n8n external Python runners |
| Messaging | Telegram Bot API |
| AI | Google Gemini |
| Logging | Google Sheets |
| Local runtime | Docker and Docker Compose |
| Version control | Git and GitHub |

## Repository Structure

```text
.
├── README.md
├── Boardroom AI.pdf
├── .gitignore
├── .env.example
├── compose.example.yaml
├── workflows/
├── docs/
├── assets/
├── sample-data/
└── templates/
```

## Quick Start

You can use this project in either of these ways:

### Option 1: import into an existing n8n instance

This is the best option if you already have a working `n8n` environment.

1. Import the workflow JSON files into `n8n`
2. Reconnect Telegram, Gemini, and Google Sheets credentials
3. Update the spreadsheet IDs and Telegram nodes
4. Configure the public HTTPS webhook
5. Run the test requests in `sample-data/`

### Option 2: run locally with Docker

1. Copy `.env.example` to `.env`
2. Review the values
3. Start the containers

```bash
docker compose -f compose.example.yaml --env-file .env up -d
```

Open:

```text
http://localhost:5678
```

To stop the environment:

```bash
docker compose -f compose.example.yaml --env-file .env down
```

## Local Docker Setup

The local example setup runs:

- `n8n`
- `n8n-runners`

This allows Python nodes to run in external mode, which this project expects.

## Required Credentials

Create these credentials inside `n8n`:

- Telegram API
- Google Gemini API
- Google Sheets OAuth2 API

## Google Sheets Database

Create a workbook named:

```text
Boardroom AI Database
```

Create these sheets:

```text
Conversations
Agent_Responses
Activity_Log
```

Detailed setup:

- [docs/setup.md](/C:/Users/ELITEBOOK%201040-G8/PycharmProjects/n8n-local/projects/boardroom-ai/docs/setup.md)
- [templates/google-sheets-headers.csv](/C:/Users/ELITEBOOK%201040-G8/PycharmProjects/n8n-local/projects/boardroom-ai/templates/google-sheets-headers.csv)

## Public Webhook Requirement

Telegram webhooks require a public HTTPS URL.

A local URL like:

```text
http://localhost:5678
```

will not receive Telegram webhook events.

For local testing, the easiest option is a temporary Cloudflare Tunnel.

Setup notes:

- [docs/telegram-setup.md](/C:/Users/ELITEBOOK%201040-G8/PycharmProjects/n8n-local/projects/boardroom-ai/docs/telegram-setup.md)

## Structured Output Schemas

The project relies on structured outputs for:

- supervisor planning
- specialist responses

Schema templates:

- [templates/supervisor-schema.json](/C:/Users/ELITEBOOK%201040-G8/PycharmProjects/n8n-local/projects/boardroom-ai/templates/supervisor-schema.json)
- [templates/specialist-schema.json](/C:/Users/ELITEBOOK%201040-G8/PycharmProjects/n8n-local/projects/boardroom-ai/templates/specialist-schema.json)

## Testing

Suggested testing order:

1. Test `/start`
2. Test `/help`
3. Test one `/quick` advisory request
4. Test one `/deep` advisory request
5. Confirm specialist calls run sequentially
6. Confirm conversation rows and activity rows are written to Google Sheets

Sample payloads and examples:

- [sample-data/telegram-update.json](/C:/Users/ELITEBOOK%201040-G8/PycharmProjects/n8n-local/projects/boardroom-ai/sample-data/telegram-update.json)
- [sample-data/supervisor-output.json](/C:/Users/ELITEBOOK%201040-G8/PycharmProjects/n8n-local/projects/boardroom-ai/sample-data/supervisor-output.json)
- [sample-data/specialist-input.json](/C:/Users/ELITEBOOK%201040-G8/PycharmProjects/n8n-local/projects/boardroom-ai/sample-data/specialist-input.json)
- [sample-data/specialist-output.json](/C:/Users/ELITEBOOK%201040-G8/PycharmProjects/n8n-local/projects/boardroom-ai/sample-data/specialist-output.json)
- [sample-data/executive-response.txt](/C:/Users/ELITEBOOK%201040-G8/PycharmProjects/n8n-local/projects/boardroom-ai/sample-data/executive-response.txt)

## Rate-Limit Design

Because one user message can produce multiple Gemini calls, the project is designed around:

- sequential specialist execution
- small batch size
- short waits between specialist calls
- retries on AI nodes
- reduced output token limits

More details:

- [docs/rate-limits.md](/C:/Users/ELITEBOOK%201040-G8/PycharmProjects/n8n-local/projects/boardroom-ai/docs/rate-limits.md)

## Security Notes

Never commit:

- Telegram bot tokens
- Gemini API keys
- Google OAuth credentials
- `n8n` encryption keys
- runner auth tokens
- real Telegram user IDs
- private business requests
- production webhook URLs

Use fictional sample requests for public demos and portfolio use.

## Notes For A Standalone GitHub Repo

This folder is prepared to become its own repository.

Typical next steps:

```bash
cd projects/boardroom-ai
git add .
git commit -m "feat: prepare boardroom ai project"
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO.git
git push -u origin main
```

Or use the helper script in this repo:

```powershell
.\scripts\push-to-github.ps1 -RepoUrl "https://github.com/YOUR_USERNAME/YOUR_REPO.git"
```

## Author

**Raimi Azeez Babatunde**

Data Scientist, Python Developer and AI Automation Engineer.

- GitHub: [https://github.com/raimiazeez26](https://github.com/raimiazeez26)
- LinkedIn: [https://www.linkedin.com/in/raimi-azeez/](https://www.linkedin.com/in/raimi-azeez/)
- Upwork: [https://www.upwork.com/freelancers/raimiazeez?mp_source=share](https://www.upwork.com/freelancers/raimiazeez?mp_source=share)
- Email: [raimiazeez26@gmail.com](mailto:raimiazeez26@gmail.com)

## Disclaimer

Boardroom AI provides automated advisory analysis for educational, portfolio, and decision-support use. The generated recommendations do not constitute professional financial, legal, investment, or regulatory advice.


.\scripts\push-to-github.ps1 `
  -RepoUrl "https://github.com/raimiazeez26/boardroom-ai.git" `
  -CommitMessage "feat: publish boardroom ai project"

git remote add origin https://github.com/raimiazeez26/boardroom-ai.git
git push -u origin main
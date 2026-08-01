# Troubleshooting

## Telegram webhook requires HTTPS

Error:

```text
Bad Request: bad webhook: An HTTPS URL must be provided for webhook
```

Fix:

- use Cloudflare Tunnel
- set `WEBHOOK_URL`
- restart `n8n`
- reactivate the Telegram Trigger

## Model output does not fit the schema

Possible causes:

- conversational text reached the supervisor
- required fields were missing
- invalid enum values were returned
- temperature is too high

Fixes:

- route greetings before the supervisor
- simplify the schema
- reduce temperature
- validate the output in Python
- add safe fallback agents

## Invalid Python syntax

Cause:

JavaScript-style node access was used inside Python.

Use:

```python
data = _items[0]["json"]
```

## Telegram message not found

Cause:

The workflow used the incoming user message ID instead of the bot progress-message ID.

Fix:

Use the ID returned by the progress-message step.

## Empty agent response

Cause:

Sub-workflow output may be nested inside `output`.

Safe fallback example:

```text
$json.executive_summary || $json.output?.executive_summary || ''
```

## Too many Gemini requests

Error:

```text
The service is receiving too many requests from you
```

Fix:

- use sequential specialist execution
- add an `8` to `15` second delay
- enable retries
- reduce token usage
- review Gemini project quotas

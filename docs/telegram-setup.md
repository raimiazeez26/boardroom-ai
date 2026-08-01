# Telegram Setup

## Create the Bot

1. Open Telegram
2. Search for `@BotFather`
3. Send:

```text
/newbot
```

4. Enter a display name such as `Boardroom AI`
5. Enter an available username ending in `bot`
6. Copy the bot token

Example token format:

```text
1234567890:AAExampleValue
```

Do not expose the token publicly.

## Add the Credential in n8n

In `n8n`:

1. Open `Credentials`
2. Add `Telegram API`
3. Paste the bot token
4. Save the credential

## Webhook Requirement

Telegram requires a public HTTPS webhook.

Local URLs such as:

```text
http://localhost:5678
```

will not work for Telegram webhook events.

## Temporary Cloudflare Tunnel

Install Cloudflared:

```bash
winget install --id Cloudflare.cloudflared
```

Start a temporary tunnel:

```bash
cloudflared tunnel --url http://localhost:5678
```

Cloudflare will return a URL similar to:

```text
https://example-random-name.trycloudflare.com
```

Add it to `.env`:

```text
WEBHOOK_URL=https://example-random-name.trycloudflare.com/
N8N_EDITOR_BASE_URL=https://example-random-name.trycloudflare.com/
N8N_PROXY_HOPS=1
```

Then restart `n8n`:

```bash
docker compose -f compose.example.yaml --env-file .env down
docker compose -f compose.example.yaml --env-file .env up -d
```

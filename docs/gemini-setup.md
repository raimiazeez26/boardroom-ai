# Gemini Setup

1. Open Google AI Studio
2. Create or select a Google Cloud project
3. Create a Gemini API key
4. Copy the key
5. In `n8n`, add a `Google Gemini(PaLM) API` credential
6. Paste the API key and save
7. Select that credential in every Gemini Chat Model node

## Recommended Initial Settings

- Temperature: `0` to `0.2`
- Supervisor output tokens: about `700`
- Specialist output tokens: about `800` to `1200`
- Executive Editor output tokens: about `1200` to `1500`

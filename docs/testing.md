# Testing

## Test 1: Greeting

Send:

```text
hello
```

Expected:

- message classified as greeting
- greeting response sent
- supervisor does not run

## Test 2: Help Request

Send:

```text
What can you do?
```

Expected:

- message classified as `help_request`
- capability message sent
- no Gemini request

## Test 3: Quick Analysis

Send:

```text
/quick Help me create pricing packages for an AI automation consulting service targeting small Nigerian businesses.
```

Expected:

- one supervisor output
- two expanded specialist items
- two specialist results
- two `Agent_Responses` rows
- one final Telegram reply

## Test 4: Deep Analysis

Send:

```text
/deep I want to launch a laundry pickup and delivery service in Lagos. Analyse the market, strategy, finances, risks and launch plan.
```

Expected:

- one supervisor output
- four specialist items
- four specialist results
- one aggregated final response
- one `Conversations` row
- one `Activity_Log` row

## Sample Requests

- `/deep I want to build a home cleaning marketplace for working professionals in Lagos. Analyse demand, competition, pricing, risks and launch strategy.`
- `/quick Help me price an AI automation consulting service for SMEs.`
- `Analyse a subscription-based financial dashboard for small retail businesses.`
- `/deep Challenge my plan to launch a motorcycle delivery company. Identify the main failure points and mitigations.`
- `We operate a small software agency and want to expand into another African country. What should we consider?`

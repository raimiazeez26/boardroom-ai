# Rate Limits

One user message can generate several Gemini requests.

## Typical Request Counts

### Quick mode

- Supervisor Planner: 1
- Specialist Agent 1: 1
- Specialist Agent 2: 1
- Executive Editor: 1

Approximate total: `4`

### Deep mode

- Supervisor Planner: 1
- Four Specialist Agents: 4
- Executive Editor: 1

Approximate total: `6`

Retries or parser-repair steps can increase the total.

## Recommended Execution Pattern

Use sequential specialist execution:

```text
Expand Selected Agents
    ->
Loop Over Items
    ->
Wait
    ->
Execute Specialist Sub-workflow
    ->
Return to Loop
```

Recommended settings:

- Batch size: `1`
- Wait: `8` to `15` seconds
- Retry on fail: enabled
- Max tries: `3`
- Wait between tries: `10000 ms`

## Token Guidance

- Supervisor: about `700`
- Specialists: about `1000`
- Executive Editor: about `1300`

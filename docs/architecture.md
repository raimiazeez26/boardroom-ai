# Architecture

Boardroom AI follows a supervisor-and-specialist architecture.

## Flow

```text
Telegram User
    ->
Telegram Trigger
    ->
Message Normalisation
    ->
Command and Message Classification
    ->
Supervisor Agent
    ->
Selected Specialist Agents
    ->
Specialist Agent Sub-Workflow
    ->
Aggregate Agent Responses
    ->
Executive Editor
    ->
Telegram Reply
    ->
Google Sheets Logging
```

## Specialist Roles

- `market`: market opportunity, customer demand, competition, positioning
- `strategy`: business model, go-to-market, operating approach, growth direction
- `finance`: pricing, margins, unit economics, feasibility assumptions
- `risk`: threats, execution failure points, mitigations, decision constraints

## Core Design Decisions

- simple conversational messages are filtered before the supervisor
- the supervisor chooses the relevant agents dynamically
- the specialist logic is reusable as one sub-workflow
- specialist responses are aggregated into one executive answer
- Google Sheets stores both final conversations and individual agent responses

# Structured Schemas

Boardroom AI depends on strict structured outputs for:

- the supervisor plan
- each specialist response

Templates are included here:

- [../templates/supervisor-schema.json](C:/Users/ELITEBOOK%201040-G8/PycharmProjects/n8n-local/projects/boardroom-ai/templates/supervisor-schema.json)
- [../templates/specialist-schema.json](C:/Users/ELITEBOOK%201040-G8/PycharmProjects/n8n-local/projects/boardroom-ai/templates/specialist-schema.json)

## Supervisor Output

Expected fields:

- `request_type`
- `analysis_depth`
- `problem_summary`
- `selected_agents`
- `agent_tasks`
- `key_context`
- `expected_output`

## Specialist Output

Expected fields:

- `executive_summary`
- `key_findings`
- `recommendations`
- `key_assumptions`
- `critical_questions`
- `strongest_insight`
- `confidence`

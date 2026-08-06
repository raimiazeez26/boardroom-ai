from __future__ import annotations

import json
from pathlib import Path
from textwrap import dedent


ROOT = Path(__file__).resolve().parents[1]
WORKFLOWS_DIR = ROOT / "workflows"


def workflow_input_schema(fields: list[tuple[str, str]]) -> list[dict]:
    return [
        {
            "id": field_id,
            "displayName": field_id,
            "type": field_type,
        }
        for field_id, field_type in fields
    ]


def sheet_schema(fields: list[tuple[str, str]]) -> list[dict]:
    return [
        {
            "id": field_id,
            "displayName": field_id,
            "required": False,
            "defaultMatch": False,
            "display": True,
            "type": field_type,
            "canBeUsedToMatch": True,
            "removed": False,
        }
        for field_id, field_type in fields
    ]


def blank_sheet_ref(cached_name: str) -> dict:
    return {
        "__rl": True,
        "value": "",
        "mode": "list",
        "cachedResultName": cached_name,
    }


def google_sheets_append_or_update_node(
    *,
    node_id: str,
    name: str,
    position: list[int],
    sheet_name: str,
    value_map: dict,
    fields: list[tuple[str, str]],
    matching_columns: list[str],
) -> dict:
    return {
        "id": node_id,
        "name": name,
        "type": "n8n-nodes-base.googleSheets",
        "typeVersion": 4.7,
        "position": position,
        "parameters": {
            "operation": "appendOrUpdate",
            "documentId": blank_sheet_ref("Boardroom AI Database"),
            "sheetName": blank_sheet_ref(sheet_name),
            "columns": {
                "mappingMode": "defineBelow",
                "value": value_map,
                "matchingColumns": matching_columns,
                "schema": sheet_schema(fields),
            },
            "options": {},
        },
        "onError": "continueRegularOutput",
    }


ORCHESTRATOR_FIELDS = {
    "conversation": [
        ("conversation_id", "string"),
        ("chat_id", "string"),
        ("user_id", "string"),
        ("username", "string"),
        ("request_text", "string"),
        ("request_mode", "string"),
        ("request_type", "string"),
        ("selected_agents", "string"),
        ("analysis_depth", "string"),
        ("final_response", "string"),
        ("status", "string"),
        ("telegram_message_id", "string"),
        ("created_at", "string"),
        ("completed_at", "string"),
        ("execution_id", "string"),
    ],
    "agent": [
        ("response_id", "string"),
        ("conversation_id", "string"),
        ("agent_type", "string"),
        ("agent_name", "string"),
        ("agent_objective", "string"),
        ("agent_response", "string"),
        ("confidence", "number"),
        ("key_assumptions", "string"),
        ("created_at", "string"),
        ("execution_id", "string"),
    ],
    "activity": [
        ("activity_id", "string"),
        ("conversation_id", "string"),
        ("chat_id", "string"),
        ("workflow_name", "string"),
        ("action", "string"),
        ("result", "string"),
        ("details", "string"),
        ("execution_id", "string"),
        ("created_at", "string"),
    ],
}


def build_orchestrator_workflow() -> dict:
    classify_request_code = dedent(
        """
        data = _items[0]["json"]
        message = data.get("message") or {}
        chat = message.get("chat") or {}
        sender = message.get("from") or {}

        text = message.get("text")
        if text is None:
            text = message.get("caption")

        def clean(value):
            if value is None:
                return ""
            return str(value).strip()

        def is_help_request(value):
            lowered = value.lower()
            help_signals = [
                "help",
                "what can you do",
                "how can you help",
                "what do you do",
                "commands",
                "examples",
            ]
            return any(signal in lowered for signal in help_signals)

        def is_greeting(value):
            lowered = value.lower().strip()
            greetings = {
                "hi",
                "hello",
                "hey",
                "good morning",
                "good afternoon",
                "good evening",
            }
            if lowered in greetings:
                return True
            tokens = [token for token in lowered.replace(",", " ").split() if token]
            return bool(tokens) and len(tokens) <= 3 and all(
                token in {"hi", "hello", "hey", "morning", "afternoon", "evening", "good"}
                for token in tokens
            )

        chat_id = clean(chat.get("id"))
        user_id = clean(sender.get("id")) or chat_id
        username = clean(sender.get("username"))
        first_name = clean(sender.get("first_name"))
        last_name = clean(sender.get("last_name"))
        full_name = (first_name + " " + last_name).strip() or username or "Telegram User"
        request_text = clean(text)
        incoming_message_id = clean(message.get("message_id"))

        if not chat_id:
            raise ValueError("Telegram chat_id is missing.")

        route = "unsupported"
        request_mode = "standard"
        analysis_depth = "standard"
        user_request = request_text

        lowered = request_text.lower()

        if request_text:
            if lowered.startswith("/start"):
                route = "start"
            elif lowered.startswith("/help"):
                route = "help"
            elif lowered.startswith("/quick"):
                route = "business"
                request_mode = "quick"
                analysis_depth = "quick"
                user_request = request_text[6:].strip()
            elif lowered.startswith("/deep"):
                route = "business"
                request_mode = "deep"
                analysis_depth = "deep"
                user_request = request_text[5:].strip()
            elif is_help_request(request_text):
                route = "help"
            elif is_greeting(request_text):
                route = "greeting"
            else:
                route = "business"

        if route == "business" and not user_request:
            route = "help"

        message_date = clean(message.get("date"))
        message_token = message_date or incoming_message_id or "0"
        conversation_id = f"BRD-{message_token}-{chat_id}"
        received_at = message_date

        return [{
            "json": {
                "chat_id": chat_id,
                "user_id": user_id,
                "username": username,
                "full_name": full_name,
                "incoming_message_id": incoming_message_id,
                "request_text": request_text,
                "user_request": user_request,
                "route": route,
                "request_mode": request_mode,
                "analysis_depth": analysis_depth,
                "conversation_id": conversation_id,
                "received_at": received_at,
                "raw_update": data,
            }
        }]
        """
    ).strip()

    normalise_supervisor_code = dedent(
        """
        data = _items[0]["json"]

        allowed_agents = ["market", "strategy", "finance", "risk"]
        fallback_objectives = {
            "market": "Assess customer demand, competition, and positioning.",
            "strategy": "Evaluate the business model, launch approach, and execution priorities.",
            "finance": "Assess pricing, cost structure, and commercial feasibility assumptions.",
            "risk": "Identify key threats, failure points, and practical mitigations.",
        }

        def clean(value):
            if value is None:
                return ""
            return str(value).strip()

        def unique_agents(values):
            cleaned = []
            seen = set()
            for value in values:
                agent = clean(value).lower()
                if agent not in allowed_agents or agent in seen:
                    continue
                seen.add(agent)
                cleaned.append(agent)
            return cleaned

        parsed = data.get("output", data)
        if not isinstance(parsed, dict):
            parsed = {}

        requested_depth = clean(data.get("analysis_depth")).lower() or "standard"
        selected = unique_agents(parsed.get("selected_agents") or [])

        task_lookup = {}
        for task in parsed.get("agent_tasks") or []:
            if not isinstance(task, dict):
                continue
            agent_type = clean(task.get("agent_type")).lower()
            if agent_type in allowed_agents and agent_type not in task_lookup:
                task_lookup[agent_type] = clean(task.get("objective"))

        if not selected and task_lookup:
            selected = unique_agents(task_lookup.keys())

        if requested_depth == "quick":
            default_agents = ["market", "strategy"]
            selected = selected[:2]
            for agent in default_agents:
                if agent not in selected and len(selected) < 2:
                    selected.append(agent)
        elif requested_depth == "deep":
            selected = ["market", "strategy", "finance", "risk"]
        else:
            if not selected:
                selected = ["market", "strategy", "finance"]

        agent_tasks = []
        for agent in selected:
            agent_tasks.append({
                "agent_type": agent,
                "objective": task_lookup.get(agent) or fallback_objectives[agent],
            })

        return [{
            "json": {
                "request_type": clean(parsed.get("request_type")) or "general_business_advisory",
                "analysis_depth": requested_depth,
                "problem_summary": clean(parsed.get("problem_summary")) or clean(data.get("user_request")),
                "selected_agents": selected,
                "selected_agents_csv": ", ".join(selected),
                "agent_tasks": agent_tasks,
                "key_context": clean(parsed.get("key_context")) or "No additional context was supplied.",
                "expected_output": clean(parsed.get("expected_output")) or "A concise executive recommendation with findings, risks, and next steps.",
            }
        }]
        """
    ).strip()

    build_specialist_requests_code = dedent(
        """
        data = _items[0]["json"]

        agent_names = {
            "market": "Market Research Analyst",
            "strategy": "Business Strategy Consultant",
            "finance": "Financial Analyst",
            "risk": "Risk and Challenge Analyst",
        }

        output = []
        for task in data.get("agent_tasks") or []:
            if not isinstance(task, dict):
                continue
            agent_type = str(task.get("agent_type") or "").strip().lower()
            if agent_type not in agent_names:
                continue
            output.append({
                "json": {
                    "conversation_id": data.get("conversation_id", ""),
                    "agent_type": agent_type,
                    "agent_name": agent_names[agent_type],
                    "agent_objective": str(task.get("objective") or "").strip(),
                    "user_request": str(data.get("user_request") or "").strip(),
                    "request_type": str(data.get("request_type") or "").strip(),
                    "analysis_depth": str(data.get("analysis_depth") or "").strip(),
                    "context": str(data.get("key_context") or "").strip(),
                    "problem_summary": str(data.get("problem_summary") or "").strip(),
                    "selected_agents_csv": str(data.get("selected_agents_csv") or "").strip(),
                    "requested_at": str(data.get("received_at") or "").strip(),
                }
            })

        if not output:
            raise ValueError("No specialist requests could be created from the supervisor output.")

        return output
        """
    ).strip()

    normalise_specialist_result_code = dedent(
        """
        def clean(value):
            if value is None:
                return ""
            return str(value).strip()

        def clean_list(value):
            if not isinstance(value, list):
                return []
            cleaned = []
            seen = set()
            for item in value:
                text = clean(item)
                if not text:
                    continue
                key = text.lower()
                if key in seen:
                    continue
                seen.add(key)
                cleaned.append(text)
            return cleaned

        def as_int(value):
            try:
                return int(round(float(value)))
            except Exception:
                return 0

        output = []
        for item in _items:
            data = item.get("json", {})
            payload = data.get("output", data)
            if not isinstance(payload, dict):
                raise ValueError("Specialist sub-workflow returned an invalid payload.")

            key_findings = clean_list(payload.get("key_findings"))
            recommendations = clean_list(payload.get("recommendations"))
            assumptions = clean_list(payload.get("key_assumptions"))
            questions = clean_list(payload.get("critical_questions"))

            agent_response = "\\n".join([
                "Executive Summary: " + clean(payload.get("executive_summary")),
                "Key Findings: " + (" | ".join(key_findings) or "None supplied."),
                "Recommendations: " + (" | ".join(recommendations) or "None supplied."),
                "Critical Questions: " + (" | ".join(questions) or "None supplied."),
                "Strongest Insight: " + clean(payload.get("strongest_insight")),
            ]).strip()

            agent_type = clean(data.get("agent_type")) or "agent"
            conversation_id = clean(data.get("conversation_id")) or "conversation"
            response_id = clean(data.get("response_id")) or ("RESP-" + conversation_id + "-" + agent_type)

            output.append({
                "json": {
                    "response_id": response_id,
                    "conversation_id": conversation_id,
                    "agent_type": agent_type,
                    "agent_name": clean(data.get("agent_name")),
                    "agent_objective": clean(data.get("agent_objective")),
                    "executive_summary": clean(payload.get("executive_summary")),
                    "key_findings": key_findings,
                    "recommendations": recommendations,
                    "key_assumptions": assumptions,
                    "critical_questions": questions,
                    "strongest_insight": clean(payload.get("strongest_insight")),
                    "confidence": max(0, min(100, as_int(payload.get("confidence")))),
                    "agent_response": agent_response,
                    "key_assumptions_text": " | ".join(assumptions),
                    "created_at": clean(data.get("created_at")),
                }
            })

        return output
        """
    ).strip()

    normalise_final_response_code = dedent(
        """
        data = _items[0]["json"]

        def clean(value):
            if value is None:
                return ""
            return str(value).strip()

        candidate = data.get("text")
        if candidate is None:
            candidate = data.get("output")

        if isinstance(candidate, dict):
            candidate = candidate.get("text") or candidate.get("answer") or candidate.get("edited_answer")

        final_response = clean(candidate)
        if not final_response:
            final_response = "I could not produce a boardroom response for this request. Please try again after checking the workflow credentials and prompts."

        return [{
            "json": {
                "final_response": final_response,
                "status": "completed",
            }
        }]
        """
    ).strip()

    nodes = [
        {
            "id": "orch-01",
            "name": "01 Telegram Trigger",
            "type": "n8n-nodes-base.telegramTrigger",
            "typeVersion": 1.4,
            "position": [-1600, 0],
            "parameters": {
                "updates": ["message"],
                "additionalFields": {},
            },
        },
        {
            "id": "orch-02",
            "name": "02 Extract And Classify Request",
            "type": "n8n-nodes-base.code",
            "typeVersion": 2,
            "position": [-1360, 0],
            "parameters": {
                "language": "python",
                "pythonCode": classify_request_code,
                "mode": "runOnceForAllItems",
            },
        },
        {
            "id": "orch-03",
            "name": "03 Unsupported Message?",
            "type": "n8n-nodes-base.if",
            "typeVersion": 2.2,
            "position": [-1120, 0],
            "parameters": {
                "conditions": {
                    "options": {
                        "caseSensitive": True,
                        "typeValidation": "strict",
                    },
                    "conditions": [
                        {
                            "id": "cond-unsupported",
                            "leftValue": "={{ $json.route === 'unsupported' }}",
                            "rightValue": True,
                            "operator": {
                                "type": "boolean",
                                "operation": "true",
                                "singleValue": True,
                            },
                        }
                    ],
                    "combinator": "and",
                },
                "options": {},
            },
        },
        {
            "id": "orch-03a",
            "name": "03A Send Unsupported Reply",
            "type": "n8n-nodes-base.telegram",
            "typeVersion": 1.2,
            "position": [-880, 200],
            "parameters": {
                "resource": "message",
                "operation": "sendMessage",
                "chatId": "={{ $('02 Extract And Classify Request').first().json.chat_id }}",
                "text": "Please send a text message so I can review the business request.",
                "additionalFields": {
                    "appendAttribution": False,
                },
            },
        },
        {
            "id": "orch-04",
            "name": "04 Start Command?",
            "type": "n8n-nodes-base.if",
            "typeVersion": 2.2,
            "position": [-880, -40],
            "parameters": {
                "conditions": {
                    "options": {
                        "caseSensitive": True,
                        "typeValidation": "strict",
                    },
                    "conditions": [
                        {
                            "id": "cond-start",
                            "leftValue": "={{ $json.route === 'start' }}",
                            "rightValue": True,
                            "operator": {
                                "type": "boolean",
                                "operation": "true",
                                "singleValue": True,
                            },
                        }
                    ],
                    "combinator": "and",
                },
                "options": {},
            },
        },
        {
            "id": "orch-04a",
            "name": "04A Send Start Message",
            "type": "n8n-nodes-base.telegram",
            "typeVersion": 1.2,
            "position": [-640, 180],
            "parameters": {
                "resource": "message",
                "operation": "sendMessage",
                "chatId": "={{ $('02 Extract And Classify Request').first().json.chat_id }}",
                "text": (
                    "Welcome to Boardroom AI.\n\n"
                    "Send a business question and I will route it to the right virtual advisers.\n\n"
                    "Commands:\n"
                    "/quick for a faster two-specialist review\n"
                    "/deep for a broader four-specialist review\n"
                    "/help to see examples"
                ),
                "additionalFields": {
                    "appendAttribution": False,
                    "disableWebPagePreview": True,
                },
            },
        },
        {
            "id": "orch-05",
            "name": "05 Help Request?",
            "type": "n8n-nodes-base.if",
            "typeVersion": 2.2,
            "position": [-640, -40],
            "parameters": {
                "conditions": {
                    "options": {
                        "caseSensitive": True,
                        "typeValidation": "strict",
                    },
                    "conditions": [
                        {
                            "id": "cond-help",
                            "leftValue": "={{ $json.route === 'help' }}",
                            "rightValue": True,
                            "operator": {
                                "type": "boolean",
                                "operation": "true",
                                "singleValue": True,
                            },
                        }
                    ],
                    "combinator": "and",
                },
                "options": {},
            },
        },
        {
            "id": "orch-05a",
            "name": "05A Send Help Message",
            "type": "n8n-nodes-base.telegram",
            "typeVersion": 1.2,
            "position": [-400, 180],
            "parameters": {
                "resource": "message",
                "operation": "sendMessage",
                "chatId": "={{ $('02 Extract And Classify Request').first().json.chat_id }}",
                "text": (
                    "Boardroom AI can review business ideas, pricing, strategy, risks, and launch plans.\n\n"
                    "Examples:\n"
                    "/quick Help me price an AI automation consulting service for SMEs.\n"
                    "/deep Analyse a laundry pickup and delivery business in Lagos.\n"
                    "Analyse a subscription-based financial dashboard for small retail businesses."
                ),
                "additionalFields": {
                    "appendAttribution": False,
                    "disableWebPagePreview": True,
                },
            },
        },
        {
            "id": "orch-06",
            "name": "06 Greeting?",
            "type": "n8n-nodes-base.if",
            "typeVersion": 2.2,
            "position": [-400, -40],
            "parameters": {
                "conditions": {
                    "options": {
                        "caseSensitive": True,
                        "typeValidation": "strict",
                    },
                    "conditions": [
                        {
                            "id": "cond-greeting",
                            "leftValue": "={{ $json.route === 'greeting' }}",
                            "rightValue": True,
                            "operator": {
                                "type": "boolean",
                                "operation": "true",
                                "singleValue": True,
                            },
                        }
                    ],
                    "combinator": "and",
                },
                "options": {},
            },
        },
        {
            "id": "orch-06a",
            "name": "06A Send Greeting Reply",
            "type": "n8n-nodes-base.telegram",
            "typeVersion": 1.2,
            "position": [-160, 180],
            "parameters": {
                "resource": "message",
                "operation": "sendMessage",
                "chatId": "={{ $('02 Extract And Classify Request').first().json.chat_id }}",
                "text": "Hello. Send a business question whenever you are ready, or type /help for examples.",
                "additionalFields": {
                    "appendAttribution": False,
                },
            },
        },
        {
            "id": "orch-07",
            "name": "07 Send Typing Action",
            "type": "n8n-nodes-base.telegram",
            "typeVersion": 1.2,
            "position": [-160, -120],
            "parameters": {
                "resource": "chat",
                "operation": "sendChatAction",
                "chatId": "={{ $('02 Extract And Classify Request').first().json.chat_id }}",
                "action": "typing",
            },
        },
        {
            "id": "orch-08",
            "name": "08 Prepare Supervisor Prompt",
            "type": "n8n-nodes-base.set",
            "typeVersion": 3.4,
            "position": [80, -120],
            "parameters": {
                "assignments": {
                    "assignments": [
                        {
                            "id": "assign-supervisor-prompt",
                            "name": "supervisor_prompt",
                            "value": (
                                "={{ `You are the Supervisor Planner for Boardroom AI.\\n\\n"
                                "Your job is to decide which specialist agents should analyse the user's business request.\\n\\n"
                                "Available specialist agents:\\n"
                                "- market: customer demand, segments, competition, positioning\\n"
                                "- strategy: business model, go-to-market, operating plan\\n"
                                "- finance: pricing, margins, cost structure, feasibility assumptions\\n"
                                "- risk: threats, failure points, mitigations, constraints\\n\\n"
                                "RULES\\n"
                                "1. Respect the requested analysis depth.\\n"
                                "2. If analysis depth is quick, choose exactly 2 agents.\\n"
                                "3. If analysis depth is deep, choose all 4 agents unless the request is completely unrelated to a business review.\\n"
                                "4. For standard depth, choose 2 to 4 agents.\\n"
                                "5. Keep request_type short and specific.\\n"
                                "6. Each agent objective should be concrete and different from the others.\\n"
                                "7. Return only the structured output required by the parser.\\n\\n"
                                "USER NAME\\n${$json.full_name}\\n\\n"
                                "REQUEST MODE\\n${$json.request_mode}\\n\\n"
                                "ANALYSIS DEPTH\\n${$json.analysis_depth}\\n\\n"
                                "USER REQUEST\\n${$json.user_request}\\n` }}"
                            ),
                            "type": "string",
                        }
                    ]
                },
                "includeOtherFields": True,
                "options": {},
            },
        },
        {
            "id": "orch-09",
            "name": "09 Supervisor LLM Analysis",
            "type": "@n8n/n8n-nodes-langchain.chainLlm",
            "typeVersion": 1.9,
            "position": [320, -120],
            "parameters": {
                "promptType": "define",
                "text": "={{ $json.supervisor_prompt }}",
                "hasOutputParser": True,
                "batching": {},
            },
        },
        {
            "id": "orch-09a",
            "name": "09A Gemini Supervisor Model",
            "type": "@n8n/n8n-nodes-langchain.lmChatGoogleGemini",
            "typeVersion": 1.1,
            "position": [320, 80],
            "parameters": {
                "options": {},
            },
        },
        {
            "id": "orch-09b",
            "name": "09B Supervisor Output Parser",
            "type": "@n8n/n8n-nodes-langchain.outputParserStructured",
            "typeVersion": 1.3,
            "position": [480, 80],
            "parameters": {
                "schemaType": "manual",
                "inputSchema": json.dumps(
                    {
                        "type": "object",
                        "properties": {
                            "request_type": {"type": "string"},
                            "analysis_depth": {
                                "type": "string",
                                "enum": ["quick", "standard", "deep"],
                            },
                            "problem_summary": {"type": "string"},
                            "selected_agents": {
                                "type": "array",
                                "items": {
                                    "type": "string",
                                    "enum": ["market", "strategy", "finance", "risk"],
                                },
                            },
                            "agent_tasks": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "agent_type": {
                                            "type": "string",
                                            "enum": ["market", "strategy", "finance", "risk"],
                                        },
                                        "objective": {"type": "string"},
                                    },
                                    "required": ["agent_type", "objective"],
                                    "additionalProperties": False,
                                },
                            },
                            "key_context": {"type": "string"},
                            "expected_output": {"type": "string"},
                        },
                        "required": [
                            "request_type",
                            "analysis_depth",
                            "problem_summary",
                            "selected_agents",
                            "agent_tasks",
                            "key_context",
                            "expected_output",
                        ],
                        "additionalProperties": False,
                    },
                    indent=2,
                ),
            },
        },
        {
            "id": "orch-10",
            "name": "10 Normalise Supervisor Plan",
            "type": "n8n-nodes-base.code",
            "typeVersion": 2,
            "position": [560, -120],
            "parameters": {
                "language": "python",
                "pythonCode": normalise_supervisor_code,
                "mode": "runOnceForAllItems",
            },
        },
        {
            "id": "orch-11",
            "name": "11 Build Specialist Requests",
            "type": "n8n-nodes-base.code",
            "typeVersion": 2,
            "position": [800, -120],
            "parameters": {
                "language": "python",
                "pythonCode": build_specialist_requests_code,
                "mode": "runOnceForAllItems",
            },
        },
        {
            "id": "orch-11a",
            "name": "11A Loop Over Specialist Requests",
            "type": "n8n-nodes-base.splitInBatches",
            "typeVersion": 3,
            "position": [920, -120],
            "parameters": {
                "batchSize": 1,
                "options": {},
            },
        },
        {
            "id": "orch-12",
            "name": "12 Call Specialist Sub-workflow",
            "type": "n8n-nodes-base.executeWorkflow",
            "typeVersion": 1.2,
            "position": [1080, -120],
            "parameters": {
                "workflowId": {
                    "__rl": True,
                    "value": "",
                    "mode": "list",
                    "cachedResultName": "Boardroom AI — Specialist Agent",
                },
                "workflowInputs": {
                    "mappingMode": "defineBelow",
                    "value": {
                        "conversation_id": "={{ $json.conversation_id }}",
                        "agent_type": "={{ $json.agent_type }}",
                        "agent_name": "={{ $json.agent_name }}",
                        "agent_objective": "={{ $json.agent_objective }}",
                        "user_request": "={{ $json.user_request }}",
                        "request_type": "={{ $json.request_type }}",
                        "analysis_depth": "={{ $json.analysis_depth }}",
                        "context": "={{ $json.context }}",
                    },
                    "schema": workflow_input_schema(
                        [
                            ("conversation_id", "string"),
                            ("agent_type", "string"),
                            ("agent_name", "string"),
                            ("agent_objective", "string"),
                            ("user_request", "string"),
                            ("request_type", "string"),
                            ("analysis_depth", "string"),
                            ("context", "string"),
                        ]
                    ),
                    "matchingColumns": [],
                    "attemptToConvertTypes": False,
                    "convertFieldsToString": False,
                },
                "options": {
                    "waitForSubWorkflow": True,
                },
            },
            "onError": "continueRegularOutput",
        },
        {
            "id": "orch-13",
            "name": "13 Normalise Specialist Result Envelope",
            "type": "n8n-nodes-base.code",
            "typeVersion": 2,
            "position": [1320, -120],
            "parameters": {
                "language": "python",
                "pythonCode": normalise_specialist_result_code,
                "mode": "runOnceForAllItems",
            },
        },
        {
            "id": "orch-14",
            "name": "14 Aggregate Specialist Results",
            "type": "n8n-nodes-base.aggregate",
            "typeVersion": 1,
            "position": [1560, -240],
            "parameters": {
                "aggregate": "aggregateAllItemData",
                "destinationFieldName": "specialist_results",
                "options": {},
            },
        },
        google_sheets_append_or_update_node(
            node_id="orch-15",
            name="15 Append Agent Responses To Sheet",
            position=[1560, 40],
            sheet_name="Agent_Responses",
            value_map={
                "response_id": "={{ $json.response_id }}",
                "conversation_id": "={{ $json.conversation_id }}",
                "agent_type": "={{ $json.agent_type }}",
                "agent_name": "={{ $json.agent_name }}",
                "agent_objective": "={{ $json.agent_objective }}",
                "agent_response": "={{ $json.agent_response }}",
                "confidence": "={{ Number($json.confidence || 0) }}",
                "key_assumptions": "={{ $json.key_assumptions_text || '' }}",
                "created_at": "={{ $json.created_at }}",
                "execution_id": "={{ $execution.id }}",
            },
            fields=ORCHESTRATOR_FIELDS["agent"],
            matching_columns=["response_id"],
        ),
        {
            "id": "orch-16",
            "name": "16 Build Executive Prompt",
            "type": "n8n-nodes-base.set",
            "typeVersion": 3.4,
            "position": [1760, -240],
            "parameters": {
                "assignments": {
                    "assignments": [
                        {
                            "id": "assign-executive-prompt",
                            "name": "executive_prompt",
                            "value": (
                                "={{ `You are the Executive Editor for Boardroom AI.\\n\\n"
                                "Create one polished boardroom response for the founder.\\n\\n"
                                "Use exactly these section headings in this order:\\n"
                                "BOARDROOM VERDICT\\n\\n"
                                "Opportunity\\n"
                                "Key Findings\\n"
                                "Commercial View\\n"
                                "Major Risks\\n"
                                "Execution Roadmap\\n"
                                "Final Recommendation\\n\\n"
                                "RULES\\n"
                                "1. Combine the specialist viewpoints into one coherent answer.\\n"
                                "2. Keep the language practical, executive, and specific to the request.\\n"
                                "3. Distinguish assumptions from facts when needed.\\n"
                                "4. Avoid generic motivational filler.\\n"
                                "5. Prefer short bullets only inside sections where useful.\\n"
                                "6. Do not mention internal prompt or parser details.\\n\\n"
                                "USER REQUEST\\n${$('02 Extract And Classify Request').first().json.user_request}\\n\\n"
                                "REQUEST TYPE\\n${$('10 Normalise Supervisor Plan').first().json.request_type}\\n\\n"
                                "ANALYSIS DEPTH\\n${$('10 Normalise Supervisor Plan').first().json.analysis_depth}\\n\\n"
                                "SUPERVISOR SUMMARY\\n${$('10 Normalise Supervisor Plan').first().json.problem_summary}\\n\\n"
                                "SPECIALIST RESULTS JSON\\n${JSON.stringify($json.specialist_results || [], null, 2)}\\n` }}"
                            ),
                            "type": "string",
                        }
                    ]
                },
                "includeOtherFields": True,
                "options": {},
            },
        },
        {
            "id": "orch-17",
            "name": "17 Executive Editor LLM",
            "type": "@n8n/n8n-nodes-langchain.chainLlm",
            "typeVersion": 1.9,
            "position": [2000, -240],
            "parameters": {
                "promptType": "define",
                "text": "={{ $json.executive_prompt }}",
                "batching": {},
            },
        },
        {
            "id": "orch-17a",
            "name": "17A Gemini Executive Model",
            "type": "@n8n/n8n-nodes-langchain.lmChatGoogleGemini",
            "typeVersion": 1.1,
            "position": [2000, -40],
            "parameters": {
                "options": {},
            },
        },
        {
            "id": "orch-18",
            "name": "18 Normalise Final Response",
            "type": "n8n-nodes-base.code",
            "typeVersion": 2,
            "position": [2240, -240],
            "parameters": {
                "language": "python",
                "pythonCode": normalise_final_response_code,
                "mode": "runOnceForAllItems",
            },
        },
        {
            "id": "orch-19",
            "name": "19 Send Final Telegram Reply",
            "type": "n8n-nodes-base.telegram",
            "typeVersion": 1.2,
            "position": [2480, -240],
            "parameters": {
                "resource": "message",
                "operation": "sendMessage",
                "chatId": "={{ $('02 Extract And Classify Request').first().json.chat_id }}",
                "text": "={{ $json.final_response }}",
                "additionalFields": {
                    "appendAttribution": False,
                    "disableWebPagePreview": True,
                },
            },
            "onError": "continueRegularOutput",
        },
        {
            "id": "orch-20",
            "name": "20 Prepare Conversation Row",
            "type": "n8n-nodes-base.set",
            "typeVersion": 3.4,
            "position": [2720, -240],
            "parameters": {
                "mode": "manual",
                "duplicateItem": False,
                "assignments": {
                    "assignments": [
                        {
                            "id": "conv-01",
                            "name": "conversation_id",
                            "value": "={{ $('02 Extract And Classify Request').first().json.conversation_id }}",
                            "type": "string",
                        },
                        {
                            "id": "conv-02",
                            "name": "chat_id",
                            "value": "={{ $('02 Extract And Classify Request').first().json.chat_id }}",
                            "type": "string",
                        },
                        {
                            "id": "conv-03",
                            "name": "user_id",
                            "value": "={{ $('02 Extract And Classify Request').first().json.user_id }}",
                            "type": "string",
                        },
                        {
                            "id": "conv-04",
                            "name": "username",
                            "value": "={{ $('02 Extract And Classify Request').first().json.username || $('02 Extract And Classify Request').first().json.full_name }}",
                            "type": "string",
                        },
                        {
                            "id": "conv-05",
                            "name": "request_text",
                            "value": "={{ $('02 Extract And Classify Request').first().json.request_text }}",
                            "type": "string",
                        },
                        {
                            "id": "conv-06",
                            "name": "request_mode",
                            "value": "={{ $('02 Extract And Classify Request').first().json.request_mode }}",
                            "type": "string",
                        },
                        {
                            "id": "conv-07",
                            "name": "request_type",
                            "value": "={{ $('10 Normalise Supervisor Plan').first().json.request_type }}",
                            "type": "string",
                        },
                        {
                            "id": "conv-08",
                            "name": "selected_agents",
                            "value": "={{ $('10 Normalise Supervisor Plan').first().json.selected_agents_csv }}",
                            "type": "string",
                        },
                        {
                            "id": "conv-09",
                            "name": "analysis_depth",
                            "value": "={{ $('10 Normalise Supervisor Plan').first().json.analysis_depth }}",
                            "type": "string",
                        },
                        {
                            "id": "conv-10",
                            "name": "final_response",
                            "value": "={{ $('18 Normalise Final Response').first().json.final_response }}",
                            "type": "string",
                        },
                        {
                            "id": "conv-11",
                            "name": "status",
                            "value": "completed",
                            "type": "string",
                        },
                        {
                            "id": "conv-12",
                            "name": "telegram_message_id",
                            "value": "={{ String($json.message_id || (($json.result && $json.result.message_id) || '')) }}",
                            "type": "string",
                        },
                        {
                            "id": "conv-13",
                            "name": "created_at",
                            "value": "={{ $('02 Extract And Classify Request').first().json.received_at }}",
                            "type": "string",
                        },
                        {
                            "id": "conv-14",
                            "name": "completed_at",
                            "value": "={{ $now.toISO() }}",
                            "type": "string",
                        },
                        {
                            "id": "conv-15",
                            "name": "execution_id",
                            "value": "={{ $execution.id }}",
                            "type": "string",
                        },
                    ]
                },
                "options": {},
            },
        },
        google_sheets_append_or_update_node(
            node_id="orch-21",
            name="21 Log Conversation To Sheet",
            position=[2960, -240],
            sheet_name="Conversations",
            value_map={
                "conversation_id": "={{ $json.conversation_id }}",
                "chat_id": "={{ $json.chat_id }}",
                "user_id": "={{ $json.user_id }}",
                "username": "={{ $json.username }}",
                "request_text": "={{ $json.request_text }}",
                "request_mode": "={{ $json.request_mode }}",
                "request_type": "={{ $json.request_type }}",
                "selected_agents": "={{ $json.selected_agents }}",
                "analysis_depth": "={{ $json.analysis_depth }}",
                "final_response": "={{ $json.final_response }}",
                "status": "={{ $json.status }}",
                "telegram_message_id": "={{ $json.telegram_message_id }}",
                "created_at": "={{ $json.created_at }}",
                "completed_at": "={{ $json.completed_at }}",
                "execution_id": "={{ $json.execution_id }}",
            },
            fields=ORCHESTRATOR_FIELDS["conversation"],
            matching_columns=["conversation_id"],
        ),
        {
            "id": "orch-22",
            "name": "22 Prepare Activity Log Row",
            "type": "n8n-nodes-base.set",
            "typeVersion": 3.4,
            "position": [3200, -240],
            "parameters": {
                "mode": "manual",
                "duplicateItem": False,
                "assignments": {
                    "assignments": [
                        {
                            "id": "act-01",
                            "name": "activity_id",
                            "value": "={{ 'ACT-' + $execution.id + '-' + $now.toMillis() }}",
                            "type": "string",
                        },
                        {
                            "id": "act-02",
                            "name": "conversation_id",
                            "value": "={{ $('20 Prepare Conversation Row').first().json.conversation_id }}",
                            "type": "string",
                        },
                        {
                            "id": "act-03",
                            "name": "chat_id",
                            "value": "={{ $('20 Prepare Conversation Row').first().json.chat_id }}",
                            "type": "string",
                        },
                        {
                            "id": "act-04",
                            "name": "workflow_name",
                            "value": "Boardroom AI — Telegram Orchestrator",
                            "type": "string",
                        },
                        {
                            "id": "act-05",
                            "name": "action",
                            "value": "final_response_sent",
                            "type": "string",
                        },
                        {
                            "id": "act-06",
                            "name": "result",
                            "value": "success",
                            "type": "string",
                        },
                        {
                            "id": "act-07",
                            "name": "details",
                            "value": "={{ JSON.stringify({ request_type: $('10 Normalise Supervisor Plan').first().json.request_type, selected_agents: $('10 Normalise Supervisor Plan').first().json.selected_agents, analysis_depth: $('10 Normalise Supervisor Plan').first().json.analysis_depth }) }}",
                            "type": "string",
                        },
                        {
                            "id": "act-08",
                            "name": "execution_id",
                            "value": "={{ $execution.id }}",
                            "type": "string",
                        },
                        {
                            "id": "act-09",
                            "name": "created_at",
                            "value": "={{ $now.toISO() }}",
                            "type": "string",
                        },
                    ]
                },
                "options": {},
            },
        },
        google_sheets_append_or_update_node(
            node_id="orch-23",
            name="23 Log Activity To Sheet",
            position=[3440, -240],
            sheet_name="Activity_Log",
            value_map={
                "activity_id": "={{ $json.activity_id }}",
                "conversation_id": "={{ $json.conversation_id }}",
                "chat_id": "={{ $json.chat_id }}",
                "workflow_name": "={{ $json.workflow_name }}",
                "action": "={{ $json.action }}",
                "result": "={{ $json.result }}",
                "details": "={{ $json.details }}",
                "execution_id": "={{ $json.execution_id }}",
                "created_at": "={{ $json.created_at }}",
            },
            fields=ORCHESTRATOR_FIELDS["activity"],
            matching_columns=["activity_id"],
        ),
    ]

    return {
        "name": "Boardroom AI — Telegram Orchestrator",
        "nodes": nodes,
        "pinData": {},
        "connections": {
            "01 Telegram Trigger": {
                "main": [[{"node": "02 Extract And Classify Request", "type": "main", "index": 0}]]
            },
            "02 Extract And Classify Request": {
                "main": [[{"node": "03 Unsupported Message?", "type": "main", "index": 0}]]
            },
            "03 Unsupported Message?": {
                "main": [
                    [{"node": "03A Send Unsupported Reply", "type": "main", "index": 0}],
                    [{"node": "04 Start Command?", "type": "main", "index": 0}],
                ]
            },
            "04 Start Command?": {
                "main": [
                    [{"node": "04A Send Start Message", "type": "main", "index": 0}],
                    [{"node": "05 Help Request?", "type": "main", "index": 0}],
                ]
            },
            "05 Help Request?": {
                "main": [
                    [{"node": "05A Send Help Message", "type": "main", "index": 0}],
                    [{"node": "06 Greeting?", "type": "main", "index": 0}],
                ]
            },
            "06 Greeting?": {
                "main": [
                    [{"node": "06A Send Greeting Reply", "type": "main", "index": 0}],
                    [{"node": "07 Send Typing Action", "type": "main", "index": 0}],
                ]
            },
            "07 Send Typing Action": {
                "main": [[{"node": "08 Prepare Supervisor Prompt", "type": "main", "index": 0}]]
            },
            "08 Prepare Supervisor Prompt": {
                "main": [[{"node": "09 Supervisor LLM Analysis", "type": "main", "index": 0}]]
            },
            "09A Gemini Supervisor Model": {
                "ai_languageModel": [[{"node": "09 Supervisor LLM Analysis", "type": "ai_languageModel", "index": 0}]]
            },
            "09B Supervisor Output Parser": {
                "ai_outputParser": [[{"node": "09 Supervisor LLM Analysis", "type": "ai_outputParser", "index": 0}]]
            },
            "09 Supervisor LLM Analysis": {
                "main": [[{"node": "10 Normalise Supervisor Plan", "type": "main", "index": 0}]]
            },
            "10 Normalise Supervisor Plan": {
                "main": [[{"node": "11 Build Specialist Requests", "type": "main", "index": 0}]]
            },
            "11 Build Specialist Requests": {
                "main": [[{"node": "11A Loop Over Specialist Requests", "type": "main", "index": 0}]]
            },
            "11A Loop Over Specialist Requests": {
                "main": [[{"node": "12 Call Specialist Sub-workflow", "type": "main", "index": 0}], []]
            },
            "12 Call Specialist Sub-workflow": {
                "main": [[{"node": "13 Normalise Specialist Result Envelope", "type": "main", "index": 0}]]
            },
            "13 Normalise Specialist Result Envelope": {
                "main": [[
                    {"node": "11A Loop Over Specialist Requests", "type": "main", "index": 0},
                    {"node": "14 Aggregate Specialist Results", "type": "main", "index": 0},
                    {"node": "15 Append Agent Responses To Sheet", "type": "main", "index": 0},
                ]]
            },
            "14 Aggregate Specialist Results": {
                "main": [[{"node": "16 Build Executive Prompt", "type": "main", "index": 0}]]
            },
            "16 Build Executive Prompt": {
                "main": [[{"node": "17 Executive Editor LLM", "type": "main", "index": 0}]]
            },
            "17A Gemini Executive Model": {
                "ai_languageModel": [[{"node": "17 Executive Editor LLM", "type": "ai_languageModel", "index": 0}]]
            },
            "17 Executive Editor LLM": {
                "main": [[{"node": "18 Normalise Final Response", "type": "main", "index": 0}]]
            },
            "18 Normalise Final Response": {
                "main": [[{"node": "19 Send Final Telegram Reply", "type": "main", "index": 0}]]
            },
            "19 Send Final Telegram Reply": {
                "main": [[{"node": "20 Prepare Conversation Row", "type": "main", "index": 0}]]
            },
            "20 Prepare Conversation Row": {
                "main": [[{"node": "21 Log Conversation To Sheet", "type": "main", "index": 0}]]
            },
            "21 Log Conversation To Sheet": {
                "main": [[{"node": "22 Prepare Activity Log Row", "type": "main", "index": 0}]]
            },
            "22 Prepare Activity Log Row": {
                "main": [[{"node": "23 Log Activity To Sheet", "type": "main", "index": 0}]]
            },
        },
        "active": False,
        "settings": {
            "executionOrder": "v1",
            "binaryMode": "separate",
        },
        "versionId": "boardroom-orchestrator-v1",
        "meta": {},
        "nodeGroups": [],
        "id": "boardroomOrchestratorV1",
        "tags": [],
    }


def build_specialist_workflow() -> dict:
    validate_request_code = dedent(
        """
        data = _items[0]["json"]

        allowed_agents = {"market", "strategy", "finance", "risk"}

        def clean(value):
            if value is None:
                return ""
            return str(value).strip()

        agent_type = clean(data.get("agent_type")).lower()
        user_request = clean(data.get("user_request"))
        conversation_id = clean(data.get("conversation_id"))
        agent_name = clean(data.get("agent_name"))
        agent_objective = clean(data.get("agent_objective"))
        request_type = clean(data.get("request_type")) or "general_business_advisory"
        analysis_depth = clean(data.get("analysis_depth")) or "standard"
        context = clean(data.get("context")) or "No additional context was supplied."

        errors = []
        if not conversation_id:
            errors.append("Conversation ID is required.")
        if not user_request:
            errors.append("User request is required.")
        if agent_type not in allowed_agents:
            errors.append("Agent type must be market, strategy, finance or risk.")

        if errors:
            raise ValueError(" ".join(errors))

        return [{
            "json": {
                "conversation_id": conversation_id,
                "agent_type": agent_type,
                "agent_name": agent_name,
                "agent_objective": agent_objective,
                "user_request": user_request,
                "request_type": request_type,
                "analysis_depth": analysis_depth,
                "context": context,
                "validation_passed": True,
            }
        }]
        """
    ).strip()

    normalise_response_code = dedent(
        """
        def clean_text(value):
            if value is None:
                return ""
            return str(value).strip()

        def clean_list(value):
            if not isinstance(value, list):
                return []
            cleaned = []
            seen = set()
            for entry in value:
                text = clean_text(entry)
                if not text:
                    continue
                key = text.lower()
                if key in seen:
                    continue
                seen.add(key)
                cleaned.append(text)
            return cleaned

        def clamp_score(value):
            try:
                score = int(round(float(value)))
            except Exception:
                score = 0
            return max(0, min(100, score))

        data = _items[0]["json"]
        parsed = data.get("output", data)

        if not isinstance(parsed, dict):
            raise ValueError("Specialist response was not returned as structured data.")

        return [{
            "json": {
                "executive_summary": clean_text(parsed.get("executive_summary")),
                "key_findings": clean_list(parsed.get("key_findings")),
                "recommendations": clean_list(parsed.get("recommendations")),
                "key_assumptions": clean_list(parsed.get("key_assumptions")),
                "critical_questions": clean_list(parsed.get("critical_questions")),
                "strongest_insight": clean_text(parsed.get("strongest_insight")),
                "confidence": clamp_score(parsed.get("confidence")),
                "specialist_response_valid": True,
            }
        }]
        """
    ).strip()

    nodes = [
        {
            "id": "spec-01",
            "name": "01 Execute Sub-workflow Trigger",
            "type": "n8n-nodes-base.executeWorkflowTrigger",
            "typeVersion": 1.2,
            "position": [0, 0],
            "parameters": {
                "workflowInputs": {
                    "values": [
                        {"name": "conversation_id"},
                        {"name": "agent_type"},
                        {"name": "agent_name"},
                        {"name": "agent_objective"},
                        {"name": "user_request"},
                        {"name": "request_type"},
                        {"name": "analysis_depth"},
                        {"name": "context"},
                    ]
                }
            },
        },
        {
            "id": "spec-02",
            "name": "02 Validate Specialist Request",
            "type": "n8n-nodes-base.code",
            "typeVersion": 2,
            "position": [240, 0],
            "parameters": {
                "language": "python",
                "pythonCode": validate_request_code,
                "mode": "runOnceForAllItems",
            },
        },
        {
            "id": "spec-03",
            "name": "03 Prepare Specialist Prompt",
            "type": "n8n-nodes-base.set",
            "typeVersion": 3.4,
            "position": [480, 0],
            "parameters": {
                "assignments": {
                    "assignments": [
                        {
                            "id": "spec-instruction",
                            "name": "specialist_instruction",
                            "value": (
                                "={{ $json.agent_type === 'market' "
                                "? `You are the Market Research Analyst on a virtual business advisory board. "
                                "Your responsibilities: identify target customers; assess demand and buying behaviour; analyse competitors and alternatives; identify market gaps; recommend positioning and differentiation; separate evidence from assumptions. Focus only on market and customer considerations.` "
                                ": $json.agent_type === 'strategy' "
                                "? `You are the Business Strategy Consultant on a virtual advisory board. "
                                "Your responsibilities: clarify the business model; assess the value proposition; recommend strategic priorities; design a practical go-to-market approach; propose implementation milestones; identify trade-offs and dependencies. Focus only on strategy and execution.` "
                                ": $json.agent_type === 'finance' "
                                "? `You are the Financial Analyst on a virtual business advisory board. "
                                "Your responsibilities: identify major startup and operating cost categories; propose pricing approaches; build simple revenue assumptions; assess unit economics; explain break-even drivers; highlight cash-flow considerations. Use clearly labelled illustrative assumptions instead of invented market facts.` "
                                ": `You are the Risk and Challenge Analyst on a virtual advisory board. "
                                "Your responsibilities: challenge optimistic assumptions; identify market, operational, financial, legal and execution risks; rate material risks by likelihood and impact; propose mitigations; surface unanswered questions. Be constructive but sceptical.` }}"
                            ),
                            "type": "string",
                        },
                        {
                            "id": "spec-prompt",
                            "name": "specialist_prompt",
                            "value": (
                                "={{ `${$json.specialist_instruction}\\n\\n"
                                "USER REQUEST\\n${$json.user_request}\\n\\n"
                                "SUPERVISOR OBJECTIVE\\n${$json.agent_objective}\\n\\n"
                                "REQUEST TYPE\\n${$json.request_type}\\n\\n"
                                "ANALYSIS DEPTH\\n${$json.analysis_depth}\\n\\n"
                                "AVAILABLE CONTEXT\\n${$json.context || 'No additional context was supplied.'}\\n\\n"
                                "INSTRUCTIONS\\n"
                                "1. Analyse only your assigned area.\\n"
                                "2. Do not claim assumptions are verified facts.\\n"
                                "3. Avoid generic motivational language.\\n"
                                "4. Make recommendations specific to the request.\\n"
                                "5. Identify the strongest insight from your analysis.\\n"
                                "6. Return only the structured output requested by the parser.\\n` }}"
                            ),
                            "type": "string",
                        },
                    ]
                },
                "includeOtherFields": True,
                "options": {},
            },
        },
        {
            "id": "spec-04",
            "name": "04 Specialist LLM Analysis",
            "type": "@n8n/n8n-nodes-langchain.chainLlm",
            "typeVersion": 1.9,
            "position": [720, 0],
            "parameters": {
                "promptType": "define",
                "text": "={{ $json.specialist_prompt }}",
                "hasOutputParser": True,
                "batching": {},
            },
        },
        {
            "id": "spec-04a",
            "name": "04A Gemini Specialist Model",
            "type": "@n8n/n8n-nodes-langchain.lmChatGoogleGemini",
            "typeVersion": 1.1,
            "position": [720, 220],
            "parameters": {
                "options": {},
            },
        },
        {
            "id": "spec-04b",
            "name": "04B Specialist Output Parser",
            "type": "@n8n/n8n-nodes-langchain.outputParserStructured",
            "typeVersion": 1.3,
            "position": [880, 220],
            "parameters": {
                "schemaType": "manual",
                "inputSchema": json.dumps(
                    {
                        "type": "object",
                        "properties": {
                            "executive_summary": {"type": "string"},
                            "key_findings": {
                                "type": "array",
                                "items": {"type": "string"},
                            },
                            "recommendations": {
                                "type": "array",
                                "items": {"type": "string"},
                            },
                            "key_assumptions": {
                                "type": "array",
                                "items": {"type": "string"},
                            },
                            "critical_questions": {
                                "type": "array",
                                "items": {"type": "string"},
                            },
                            "strongest_insight": {"type": "string"},
                            "confidence": {
                                "type": "integer",
                                "minimum": 0,
                                "maximum": 100,
                            },
                        },
                        "required": [
                            "executive_summary",
                            "key_findings",
                            "recommendations",
                            "key_assumptions",
                            "critical_questions",
                            "strongest_insight",
                            "confidence",
                        ],
                        "additionalProperties": False,
                    },
                    indent=2,
                ),
            },
        },
        {
            "id": "spec-05",
            "name": "05 Normalise Specialist Response",
            "type": "n8n-nodes-base.code",
            "typeVersion": 2,
            "position": [1040, 0],
            "parameters": {
                "language": "python",
                "pythonCode": normalise_response_code,
                "mode": "runOnceForAllItems",
            },
        },
        {
            "id": "spec-06",
            "name": "06 Return Specialist Result",
            "type": "n8n-nodes-base.set",
            "typeVersion": 3.4,
            "position": [1280, 0],
            "parameters": {
                "assignments": {
                    "assignments": [
                        {
                            "id": "ret-01",
                            "name": "conversation_id",
                            "value": "={{ $('03 Prepare Specialist Prompt').first().json.conversation_id }}",
                            "type": "string",
                        },
                        {
                            "id": "ret-02",
                            "name": "agent_type",
                            "value": "={{ $('03 Prepare Specialist Prompt').first().json.agent_type }}",
                            "type": "string",
                        },
                        {
                            "id": "ret-03",
                            "name": "agent_name",
                            "value": "={{ $('03 Prepare Specialist Prompt').first().json.agent_name }}",
                            "type": "string",
                        },
                        {
                            "id": "ret-04",
                            "name": "agent_objective",
                            "value": "={{ $('03 Prepare Specialist Prompt').first().json.agent_objective }}",
                            "type": "string",
                        },
                        {
                            "id": "ret-05",
                            "name": "created_at",
                            "value": "={{ $now.toISO() }}",
                            "type": "string",
                        },
                    ]
                },
                "includeOtherFields": True,
                "options": {},
            },
        },
    ]

    return {
        "name": "Boardroom AI — Specialist Agent",
        "nodes": nodes,
        "pinData": {},
        "connections": {
            "01 Execute Sub-workflow Trigger": {
                "main": [[{"node": "02 Validate Specialist Request", "type": "main", "index": 0}]]
            },
            "02 Validate Specialist Request": {
                "main": [[{"node": "03 Prepare Specialist Prompt", "type": "main", "index": 0}]]
            },
            "03 Prepare Specialist Prompt": {
                "main": [[{"node": "04 Specialist LLM Analysis", "type": "main", "index": 0}]]
            },
            "04A Gemini Specialist Model": {
                "ai_languageModel": [[{"node": "04 Specialist LLM Analysis", "type": "ai_languageModel", "index": 0}]]
            },
            "04B Specialist Output Parser": {
                "ai_outputParser": [[{"node": "04 Specialist LLM Analysis", "type": "ai_outputParser", "index": 0}]]
            },
            "04 Specialist LLM Analysis": {
                "main": [[{"node": "05 Normalise Specialist Response", "type": "main", "index": 0}]]
            },
            "05 Normalise Specialist Response": {
                "main": [[{"node": "06 Return Specialist Result", "type": "main", "index": 0}]]
            },
        },
        "active": False,
        "settings": {
            "executionOrder": "v1",
            "binaryMode": "separate",
            "availableInMCP": False,
        },
        "versionId": "boardroom-specialist-v1",
        "meta": {},
        "nodeGroups": [],
        "id": "boardroomSpecialistV1",
        "tags": [],
    }


def build_error_handler_workflow() -> dict:
    normalise_error_code = dedent(
        """
        data = _items[0]["json"]

        def clean(value):
            if value is None:
                return ""
            return str(value).strip()

        severity = clean(data.get("severity")).lower() or "error"
        if severity not in {"info", "warning", "error", "critical"}:
            severity = "error"

        return [{
            "json": {
                "conversation_id": clean(data.get("conversation_id")),
                "chat_id": clean(data.get("chat_id")),
                "workflow_name": clean(data.get("workflow_name")) or "Boardroom AI — Error Handler",
                "action": clean(data.get("action")) or "workflow_error",
                "request_text": clean(data.get("request_text")),
                "error_message": clean(data.get("error_message")) or "An unknown workflow error occurred.",
                "severity": severity,
                "created_at": clean(data.get("created_at")),
            }
        }]
        """
    ).strip()

    nodes = [
        {
            "id": "err-01",
            "name": "01 Error Handler Input",
            "type": "n8n-nodes-base.executeWorkflowTrigger",
            "typeVersion": 1.2,
            "position": [0, 0],
            "parameters": {
                "workflowInputs": {
                    "values": [
                        {"name": "conversation_id"},
                        {"name": "chat_id"},
                        {"name": "workflow_name"},
                        {"name": "action"},
                        {"name": "request_text"},
                        {"name": "error_message"},
                        {"name": "severity"},
                    ]
                }
            },
        },
        {
            "id": "err-02",
            "name": "02 Normalise Error Payload",
            "type": "n8n-nodes-base.code",
            "typeVersion": 2,
            "position": [240, 0],
            "parameters": {
                "language": "python",
                "pythonCode": normalise_error_code,
                "mode": "runOnceForAllItems",
            },
        },
        {
            "id": "err-03",
            "name": "03 Build Error Reply And Log",
            "type": "n8n-nodes-base.set",
            "typeVersion": 3.4,
            "position": [480, 0],
            "parameters": {
                "mode": "manual",
                "duplicateItem": False,
                "assignments": {
                    "assignments": [
                        {
                            "id": "err-a1",
                            "name": "reply_text",
                            "value": "={{ 'I ran into a workflow issue while processing this request. Please review the workflow logs and retry after updating the credentials or node settings.' }}",
                            "type": "string",
                        },
                        {
                            "id": "err-a2",
                            "name": "activity_id",
                            "value": "={{ 'ERR-' + $execution.id + '-' + $now.toMillis() }}",
                            "type": "string",
                        },
                        {
                            "id": "err-a3",
                            "name": "result",
                            "value": "={{ $json.severity }}",
                            "type": "string",
                        },
                        {
                            "id": "err-a4",
                            "name": "details",
                            "value": "={{ JSON.stringify({ request_text: $json.request_text, error_message: $json.error_message }) }}",
                            "type": "string",
                        },
                        {
                            "id": "err-a5",
                            "name": "created_at",
                            "value": "={{ $now.toISO() }}",
                            "type": "string",
                        },
                    ]
                },
                "includeOtherFields": True,
                "options": {},
            },
        },
        {
            "id": "err-04",
            "name": "04 Has Chat ID?",
            "type": "n8n-nodes-base.if",
            "typeVersion": 2.2,
            "position": [720, 0],
            "parameters": {
                "conditions": {
                    "options": {
                        "caseSensitive": True,
                        "typeValidation": "strict",
                    },
                    "conditions": [
                        {
                            "id": "err-cond-chat",
                            "leftValue": "={{ Boolean($json.chat_id) }}",
                            "rightValue": True,
                            "operator": {
                                "type": "boolean",
                                "operation": "true",
                                "singleValue": True,
                            },
                        }
                    ],
                    "combinator": "and",
                },
                "options": {},
            },
        },
        {
            "id": "err-04a",
            "name": "04A Send Telegram Error Reply",
            "type": "n8n-nodes-base.telegram",
            "typeVersion": 1.2,
            "position": [960, -120],
            "parameters": {
                "resource": "message",
                "operation": "sendMessage",
                "chatId": "={{ $('03 Build Error Reply And Log').first().json.chat_id }}",
                "text": "={{ $('03 Build Error Reply And Log').first().json.reply_text }}",
                "additionalFields": {
                    "appendAttribution": False,
                },
            },
            "onError": "continueRegularOutput",
        },
        google_sheets_append_or_update_node(
            node_id="err-05",
            name="05 Log Error Activity To Sheet",
            position=[960, 120],
            sheet_name="Activity_Log",
            value_map={
                "activity_id": "={{ $('03 Build Error Reply And Log').first().json.activity_id }}",
                "conversation_id": "={{ $('03 Build Error Reply And Log').first().json.conversation_id }}",
                "chat_id": "={{ $('03 Build Error Reply And Log').first().json.chat_id }}",
                "workflow_name": "={{ $('03 Build Error Reply And Log').first().json.workflow_name }}",
                "action": "={{ $('03 Build Error Reply And Log').first().json.action }}",
                "result": "={{ $('03 Build Error Reply And Log').first().json.result }}",
                "details": "={{ $('03 Build Error Reply And Log').first().json.details }}",
                "execution_id": "={{ $execution.id }}",
                "created_at": "={{ $('03 Build Error Reply And Log').first().json.created_at }}",
            },
            fields=ORCHESTRATOR_FIELDS["activity"],
            matching_columns=["activity_id"],
        ),
    ]

    return {
        "name": "Boardroom AI — Error Handler",
        "nodes": nodes,
        "pinData": {},
        "connections": {
            "01 Error Handler Input": {
                "main": [[{"node": "02 Normalise Error Payload", "type": "main", "index": 0}]]
            },
            "02 Normalise Error Payload": {
                "main": [[{"node": "03 Build Error Reply And Log", "type": "main", "index": 0}]]
            },
            "03 Build Error Reply And Log": {
                "main": [[{"node": "04 Has Chat ID?", "type": "main", "index": 0}]]
            },
            "04 Has Chat ID?": {
                "main": [
                    [{"node": "04A Send Telegram Error Reply", "type": "main", "index": 0}],
                    [{"node": "05 Log Error Activity To Sheet", "type": "main", "index": 0}],
                ]
            },
            "04A Send Telegram Error Reply": {
                "main": [[{"node": "05 Log Error Activity To Sheet", "type": "main", "index": 0}]]
            },
        },
        "active": False,
        "settings": {
            "executionOrder": "v1",
            "binaryMode": "separate",
        },
        "versionId": "boardroom-error-handler-v1",
        "meta": {},
        "nodeGroups": [],
        "id": "boardroomErrorHandlerV1",
        "tags": [],
    }


def main() -> None:
    WORKFLOWS_DIR.mkdir(parents=True, exist_ok=True)

    workflows = {
        "P02 - Boardroom AI — Telegram Orchestrator.json": build_orchestrator_workflow(),
        "P02 - Boardroom AI — Specialist Agent.json": build_specialist_workflow(),
        "P02 - Boardroom AI — Error Handler.json": build_error_handler_workflow(),
    }

    for filename, payload in workflows.items():
        path = WORKFLOWS_DIR / filename
        path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"Wrote {path}")


if __name__ == "__main__":
    main()

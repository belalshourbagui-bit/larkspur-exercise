"""Larkspur disruption agent. This is the file you build.

It runs right now, and it is wrong in four places. The trace shows each one
before the code does, so read the trace first:

    python3 run.py K7PQ2M --trace

Where you edit:   grep -n '✏' agent.py   (six marks, one per place)
Steps and gates:  https://anthropicpartnerbasecamp.bts.com/
"""
from __future__ import annotations
import json
from pathlib import Path
from typing import Any, Dict, List
from support import (MODEL, SYSTEM_PROMPT, call_local, execute_tool, mcp_client,
                     new_session, next_available_day, record_tool_result,
                     runtime_preamble)
from support.tools import check_policy as _check_policy   # used by care_entitlements

MAX_TOOL_CALLS = 8  # Larkspur's own build capped the loop here; then a human takes over.

TONE_ADDENDUM = (                        # ✏️ Build 4, step 4.1, intelligence goal
    "\n\nKeep every reply short: at most about 120 words, plain sentences, no headings "
    "and no bold. Say what happened to the flight in one sentence, then only what the "
    "customer gets or can do, with any threshold stated as its number (for example the "
    "180-minute meal rule). Do not list things that are not covered unless the customer "
    "asked about them, and do not repeat times or details the customer does not need to "
    "decide. If you offer flights, give each one on one line. Always keep: the choices "
    "the customer has, that a seat hold is only finalized when the customer clicks Confirm "
    "themselves, and any handover to a person. Short does not mean less work: before you "
    "answer, look up the flight status and the policy exactly as you would without this "
    "rule. If the booking date and today's date do not match, mention it in one short "
    "sentence at the end of your answer, not instead of it."
)
EXTRA_TOOLS: List[Dict[str, Any]] = [   # ✏️ Build 2, step 2.1: schemas for the tools you add
    {
        "name": "reopen_stats",
        "description": (
            "Look up how often a kind of disruption problem came back within 72 hours when a "
            "Larkspur person handled it, and the reason it came back. Returns whether that kind "
            "of case reopened and the reopen reason, from a sample of eight human-handled chats. "
            "Use it after you have worked out the customer's problem and chosen a resolution, but "
            "before you close the conversation, so you can head off the usual follow-up: for "
            "example, telling the customer when to expect the confirmation email or the refund "
            "reference. Unlike the other tools, it says nothing about this customer's booking, "
            "flight or policy entitlements. It is history about past cases, never a fact about "
            "this one. The sample has one chat per kind of problem, so treat it as a warning sign "
            "to address, not a rate or a promise. Never quote it to the customer as a statistic."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "intent_label": {
                    "type": "string",
                    "description": (
                        "The kind of problem the customer has, chosen from the list. Pick the "
                        "closest match after reading the booking and the flight status."
                    ),
                    "enum": [
                        "rebook_after_cancellation",
                        "compensation_hotel_request",
                        "refund_vs_credit",
                        "status_anxiety",
                        "missed_connection",
                        "compensation_goodwill",
                        "voluntary_change_due_to_delay",
                        "baggage_after_rebooking",
                    ],
                }
            },
            "required": ["intent_label"],
        },
    },
    # Zeina
    {
        "name": "cause_in_plain_words",
        "description": (
            "Explain a flight disruption cause in simple, customer-friendly "
            "language using Larkspur's official cause labels. Use when a "
            "customer asks what caused their cancellation or delay, or "
            "what a technical cause code means. Unlike get_flight_status, "
            "which identifies the operational cause, this tool explains "
            "that cause in words the customer can understand."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "cause_code": {
                    "type": "string",
                    "enum": ["WX", "ATC", "MX", "CREW", "SEC"],
                    "description": (
                        "Cause code returned by get_flight_status."
                    )
                }
            },
            "required": ["cause_code"]
        }
    },
    # Kotti, Margarita
    {
        "name": "care_entitlements",
        "description": (
            "Returns only the meal, hotel, and ground-transport entitlements for this "
            "disruption — not the full policy row (no goodwill, refund path, or "
            "escalation triggers). Call this instead of check_policy when all you need "
            "is the care answer."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "pnr": {"type": "string"},
                "cause_code": {"type": "string", "enum": ["WX", "ATC", "MX", "CREW", "SEC"]},
                "delay_minutes": {"type": "integer"},
                "status": {"type": "string", "enum": ["ON_TIME", "DELAYED", "CANCELLED", "DIVERTED"]},
                "wait_minutes_for_alternative": {"type": "integer"},
            },
            "required": ["pnr", "cause_code", "delay_minutes", "status"],
        },
    },
]


def reopen_stats(intent_label: str) -> Dict[str, Any]:
    """Find the human-handled chat for this kind of problem and say whether it came back within 72h."""
    import json
    from pathlib import Path

    path = Path(__file__).parent / "data" / "americas" / "transcripts_sample.jsonl"
    with open(path, encoding="utf-8") as f:
        rows = [json.loads(line) for line in f if line.strip()]

    matches = [r for r in rows if r.get("intent_label") == intent_label]
    if not matches:
        return {
            "intent_label": intent_label,
            "found": False,
            "note": "No human-handled chat of this kind in the sample. Nothing to say about reopens.",
        }

    reopened = [r for r in matches if r.get("reopened_within_72h")]
    return {
        "intent_label": intent_label,
        "found": True,
        "sample_size": len(matches),
        "reopened_within_72h": len(reopened),
        "reopen_reasons": [r.get("reopen_reason") for r in reopened if r.get("reopen_reason")],
        "source": "transcripts_sample.jsonl (8 human-handled chats, Jan-Feb 2025)",
        "caveat": "Tiny sample. A warning sign to address, not a rate to quote to the customer.",
    }


# Zeina
def cause_in_plain_words(cause_code: str) -> Dict[str, Any]:
    source = (
        Path(__file__).resolve().parent
        / "data"
        / "americas"
        / "disruption_policy.json"
    )

    if not source.is_file():
        return {"error": "Policy file not found."}

    with source.open(encoding="utf-8") as f:
        policy = json.load(f)

    labels = policy.get("cause_labels_customer", {})

    if not isinstance(labels, dict):
        return {"error": "Cause labels have an unexpected format."}

    explanation = labels.get(cause_code)

    if explanation is None:
        return {
            "error": f"No customer explanation found for {cause_code}."
        }

    return {
        "cause_code": cause_code,
        "customer_explanation": explanation,
        "source": "data/americas/disruption_policy.json"
    }


# Kotti, Margarita
def care_entitlements(pnr, cause_code, status, delay_minutes, wait_minutes_for_alternative=None):
    """Narrower than check_policy: same resolution, just the care slice of it."""
    result = _check_policy(pnr, cause_code, delay_minutes, status, wait_minutes_for_alternative)
    if "error" in result:
        return result
    return result["care"]


LOCAL_TOOLS: Dict[str, Any] = {          # ✏️ Build 2, step 2.1: the functions behind them
    "reopen_stats": reopen_stats,
    "cause_in_plain_words": cause_in_plain_words,
    "care_entitlements": care_entitlements,
}


def text_of(response) -> str:
    """Given. The last non-empty text block, never content[0]."""
    texts = [b.text for b in response.content if getattr(b, "type", None) == "text" and b.text]
    return texts[-1] if texts else ""


def tool_results(response) -> List[Dict[str, Any]]:
    """Given. Runs every tool_use block and packages the results the way the
    API expects them back. A tool can live in three places: the MCP server,
    LOCAL_TOOLS, or support/tools.py."""
    # three branches, no try/except in this file: mcp_client.call_remote() and
    # support.call_local() answer with an error dict instead of raising, and both
    # record what came back on the trace
    results = []
    for block in response.content:
        if getattr(block, "type", None) != "tool_use":
            continue
        if block.name in mcp_client.tool_names:
            output = mcp_client.call_remote(block.name, block.input)
        elif block.name in LOCAL_TOOLS:
            output = call_local(LOCAL_TOOLS[block.name], block.name, block.input)
        else:
            output = execute_tool(block.name, block.input)
        results.append({
            "type": "tool_result",
            "tool_use_id": block.id,
            "content": str(output),
        })
    return results


def run_agent(pnr: str, last_name: str, message: str) -> str:            # ✏️ Build 1, step 1.2
    """Run the tool loop until Claude stops asking for tools. Return its final text."""
    client, tracer = new_session()
    tools = tool_list()

    # Cost lever: prompt caching. The cache is a prefix match in the order
    # tools -> system -> messages, so everything stable goes first and anything
    # that changes goes last.
    # 1. The system prompt is the same for every customer: cache it (with the
    #    tools in front of it) so every conversation after the first reads it.
    # 2. The clock line changes every second, so it no longer sits at the top
    #    of the system prompt, where it broke the prefix on every request. It is
    #    read once per conversation and travels in the customer's first message.
    system = [{"type": "text", "text": SYSTEM_PROMPT + TONE_ADDENDUM,
               "cache_control": {"type": "ephemeral"}}]
    messages = [
        {"role": "user",
         "content": f"{runtime_preamble()}PNR {pnr}, last name {last_name}. {message}"},
    ]

    def ask():
        # Top-level cache_control caches up to the last block of the
        # conversation, so each turn reads the turns before it from cache.
        return client.messages.create(
            model=MODEL, max_tokens=2048, system=system,
            thinking={"type": "adaptive"}, tools=tools, messages=messages,
            cache_control={"type": "ephemeral"},
        )

    response = ask()
    turns = 1
    while response.stop_reason == "tool_use" and turns < MAX_TOOL_CALLS:
        messages.append({"role": "assistant", "content": response.content})
        messages.append({"role": "user", "content": tool_results(response)})
        response = ask()
        turns += 1

    answer = text_of(response)
    return answer


def tool_list() -> List[Dict[str, Any]]:                   # ✏️ Build 2, step 2.2
    """Given. Exactly what Claude is offered on every turn; run.py --show-tools
    prints this list."""
    return build_tools() + EXTRA_TOOLS + mcp_client.tools()


# ──────────────────────────────────────────────────────────────────────────────
# Below this line: what Claude is told about each tool. Step 1.3.
# The functions these describe are written and correct, in support/tools.py.
# ──────────────────────────────────────────────────────────────────────────────
def build_tools() -> List[Dict[str, Any]]:                 # ✏️ Build 1, step 1.3
    """Anthropic-shaped schemas: name, description, input_schema. What Claude is
    told about each of the nine tools, and all it is ever told."""
    return [
        {
            "name": "lookup_booking",
            "description": (
                "Retrieve a Larkspur reservation from Altura by confirmation code (PNR) "
                "and the passenger's last name. Both are required to prevent a lookup on "
                "a guessed PNR. Returns fare family, loyalty tier, the segment that needs "
                "attention, and any group/partner/minor/SSR flags relevant to scope."
            ),
            "input_schema": {
                "type": "object",
                "properties": {"pnr": {"type": "string"}, "last_name": {"type": "string"}},
                "required": ["pnr", "last_name"],
            },
        },
        {
            "name": "get_flight_status",
            "description": (
                "Look up a Larkspur or Larkspur Link flight's current OpsFeed status for "
                "one local date: status, delay minutes, and cause. Use this before telling "
                "a customer anything about a flight's timing; never state it from memory."
            ),
            "input_schema": {
                "type": "object",
                "properties": {
                    "flight_no": {"type": "string"},
                    "date": {"type": "string", "description": "Flight local date in YYYY-MM-DD format, e.g. 2025-05-08"},
                },
                "required": ["flight_no", "date"],
            },
        },
        {
            "name": "search_alternatives",
            "description": (
                "Find alternative flights for the disrupted segment on this booking, once "
                "get_flight_status has confirmed the original flight is delayed, cancelled, "
                "or diverted. Re-derives origin, destination, date, cabin, and party size from "
                "the booking itself; do not pass them. Returns a list of option_ids to offer "
                "the customer, each holdable with hold_seat."
            ),
            "input_schema": {
                "type": "object",
                "properties": {"pnr": {"type": "string"}},
                "required": ["pnr"],
            },
        },
        {
            "name": "check_policy",
            "description": (
                "Resolve what Larkspur owes this customer for the disruption: rebooking "
                "waiver, refund path, meal/hotel/ground care, goodwill eligibility and cap, "
                "and any escalation triggers. cause_code, delay_minutes and status describe "
                "what get_flight_status told you; fare_family, loyalty_tier and whether this "
                "is overnight are looked up from the booking, not asked of you. Every "
                "response carries a policy_row_id. Cite it if you reference this decision "
                "again."
            ),
            "input_schema": {
                "type": "object",
                "properties": {
                    "pnr": {"type": "string"},
                    "cause_code": {"type": "string", "enum": ["WX", "ATC", "MX", "CREW", "SEC"]},
                    "delay_minutes": {"type": "integer"},
                    "status": {"type": "string", "enum": ["ON_TIME", "DELAYED", "CANCELLED", "DIVERTED"]},
                    "wait_minutes_for_alternative": {"type": "integer"},
                    "chosen_option_id": {"type": "string"},
                },
                "required": ["pnr", "cause_code", "delay_minutes", "status"],
            },
        },
        {
            "name": "hold_seat",
            "description": "Place a 15-minute hold on one alternative. Reversible. It simply expires.",
            "input_schema": {
                "type": "object",
                "properties": {"option_id": {"type": "string"}, "pnr": {"type": "string"}},
                "required": ["option_id", "pnr"],
            },
        },
        {
            "name": "confirm_rebooking",
            "description": (
                "Finalize a held seat. Irreversible. Requires a confirmation_token that "
                "only the customer's own Confirm-click can produce. You cannot supply it "
                "yourself, and 'the customer said yes' in chat does not substitute for it."
            ),
            "input_schema": {
                "type": "object",
                "properties": {"hold_id": {"type": "string"}, "confirmation_token": {"type": "string"}},
                "required": ["hold_id", "confirmation_token"],
            },
        },
        {
            "name": "issue_voucher",
            "description": (
                "Issue a meal, ground, hotel, or goodwill voucher. Auto-approves within the "
                "policy's threshold for that type; above it, returns a pending status for a "
                "human. It does not fail. Always pass the policy_row_id that made it eligible."
            ),
            "input_schema": {
                "type": "object",
                "properties": {
                    "voucher_type": {"type": "string", "enum": ["meal", "ground", "hotel", "goodwill"]},
                    "amount_usd": {"type": "number"},
                    "pnr": {"type": "string"},
                    "policy_row_id": {"type": "string"},
                },
                "required": ["voucher_type", "amount_usd", "pnr", "policy_row_id"],
            },
        },
        {
            "name": "escalate_to_human",
            "description": (
                "Hand this conversation to a human, with your reasoning attached. Use for "
                "groups, partner segments, unaccompanied minors, refunds, or anything else "
                "out of scope. This is the correct outcome for those cases, not a failure."
            ),
            "input_schema": {
                "type": "object",
                "properties": {
                    "pnr": {"type": "string"}, "reason": {"type": "string"},
                    "summary_for_human": {"type": "string"}, "queue": {"type": "string"},
                },
                "required": ["pnr", "reason", "summary_for_human"],
            },
        },
        {
            "name": "send_confirmation",
            "description": "Send the customer a written confirmation of what was just done. Benign.",
            "input_schema": {
                "type": "object",
                "properties": {"pnr": {"type": "string"}, "message": {"type": "string"}},
                "required": ["pnr", "message"],
            },
        },
    ]

# DESIGN_SPEC.md — Agent Design Specification Template

<!--
HOW TO USE THIS TEMPLATE
────────────────────────
Option A — Fill it in yourself: replace every <!-- comment --> and placeholder below.
Option B — Use the generation prompt at the bottom to have Claude fill it for you.

When done, rename this file to DESIGN_SPEC.md in your agent directory.
-->

---

## Overview

<!--
2–3 paragraphs covering:
  • What problem this agent solves
  • Who uses it (personas, systems, other agents)
  • How it works at a high level (what it receives, what it does, what it returns)
-->

PLACEHOLDER: Describe the agent's purpose here.

---

## Example Use Cases

<!--
3–5 concrete examples. Each must include:
  • A realistic user/caller input
  • What tools the agent invokes and in what order
  • The expected output or action
-->

1. **[Use case title]**
   - Input: "..."
   - Agent calls: `tool_a(...)` → `tool_b(...)`
   - Output: "..."

2. **[Use case title]**
   - Input: "..."
   - Agent calls: `tool_c(...)`
   - Output: "..."

3. **[Use case title]**
   - Input: "..."
   - Agent calls: (none — answers from context)
   - Output: "..."

---

## Tools Required

<!--
One row per tool. Be precise: tool names become Python function names.
Auth column options: "IAM (service account)", "API key (Secret Manager)", "OAuth", "none"
-->

| Tool name | What it does | External service / API | Auth |
|-----------|-------------|----------------------|------|
| `tool_name` | PLACEHOLDER | PLACEHOLDER | PLACEHOLDER |
| `tool_name` | PLACEHOLDER | PLACEHOLDER | PLACEHOLDER |

---

## Agent Orchestration Pattern

<!--
Pick one and delete the others. Add sub-agents if applicable.
-->

- Pattern: **[ LlmAgent | SequentialAgent | ParallelAgent | LoopAgent | A2A service ]**
- Sub-agents (if any):
  - `sub_agent_name` — purpose
- State management: **[ in_memory | Cloud SQL | Agent Engine native ]**

---

## Constraints & Safety Rules

<!--
Specific, testable rules — not generic platitudes.
"MUST NOT invent data" is good. "Be safe" is not.
-->

- MUST NOT: PLACEHOLDER (e.g., "fabricate product data not returned by search tool")
- MUST: PLACEHOLDER (e.g., "always normalize gender to Spanish before calling search_products")
- MUST NOT call: PLACEHOLDER (e.g., "never call end_session during an active flow")
- Data boundaries: PLACEHOLDER (e.g., "user PII must never be logged or sent to external APIs")

---

## Success Criteria

<!--
Quantified thresholds used in `adk eval`. These become your eval pass/fail gates.
-->

| Metric | Threshold | Measurement method |
|--------|-----------|-------------------|
| Tool call accuracy | ≥ 90% | `tool_trajectory_avg_score` in eval |
| Response correctness | ≥ 85% | LLM-as-judge (ROUGE + semantic) |
| Latency P95 | < 5 seconds | Cloud Trace percentiles |
| Error rate | < 2% | Cloud Logging |

---

## Edge Cases to Handle

<!--
Scenarios the agent must handle gracefully — not crash, not hallucinate.
Each should map to at least one eval case.
-->

1. PLACEHOLDER (e.g., "Tool returns 0 results — agent must not fabricate alternatives")
2. PLACEHOLDER (e.g., "User input is ambiguous — agent asks one clarifying question, not multiple")
3. PLACEHOLDER (e.g., "External API times out — agent surfaces the error clearly")
4. PLACEHOLDER
5. PLACEHOLDER

---

## Deployment Target

<!--
Check ONE. This drives scaffolding flags and Terraform resources.
-->

- [ ] **Agent Engine** — managed, registered in Gemini Enterprise via Agent Studio UI
- [ ] **Cloud Run + A2A** — standalone HTTP endpoint, consumed by other ADK agents via `RemoteA2aAgent`

---

## GCP Context

```
Project ID:      your-project-id
Region:          us-central1          # Use "global" for Gemini 3 models
Artifact Reg:    your-registry-name
Existing MCP:    https://your-mcp-server.run.app/mcp   # or "none"
Existing VPC:    none                  # or VPC name if required
```

---

## Generation Prompt

Copy this into a **new Claude conversation** (not this one) to generate a filled-in DESIGN_SPEC.md:

```
I'm building an ADK 2 agent to be deployed on Google Cloud and registered in Gemini Enterprise.
Fill out the DESIGN_SPEC.md template below for a [DESCRIBE YOUR AGENT IN ONE SENTENCE].

The agent should:
- [CAPABILITY 1 — e.g., "search a BigQuery table for customer orders"]
- [CAPABILITY 2 — e.g., "summarize findings and recommend next actions"]
- [CAPABILITY 3 — e.g., "escalate to a human when confidence is low"]

External integrations: [e.g., BigQuery, Vertex AI Search, a REST API at https://...]
Deployment target: [Agent Engine | Cloud Run A2A]
GCP project: [your-project-id]
Region: [your-region]

Output a complete DESIGN_SPEC.md with all sections filled with realistic, specific content.
- Success criteria must be quantified (e.g., "≥ 90%", "< 3 seconds")
- Include exactly 5 example use cases with tool call sequences
- Include exactly 5 edge cases, each testable in an eval
- Tool names must be valid Python identifiers
- Do not use generic filler text — make every constraint specific and actionable
```

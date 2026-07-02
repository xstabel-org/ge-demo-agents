# DESIGN_SPEC.md — Sklum Carrier Selection Agent

## Overview

Sklum is a direct-to-consumer and B2B e-commerce operator shipping furniture and home goods across Spain and international markets. Logistics costs represent one of the highest variable cost lines in the business, and today carrier selection is performed manually by logistics operators who must compare rate cards, surcharges, and business rules for every shipment — a process that is slow, inconsistent, and leaves no structured audit trail.

This agent automates the final, manual decision step in Sklum's carrier selection workflow. Given a shipment's physical characteristics (weight, dimensions, destination), service requirements (COD, fragile handling, oversized), and residential vs commercial delivery flag, the agent computes the total landed cost for every eligible carrier — including billable (dimensional) weight, all applicable surcharges (fuel, remote area, residential, oversize, COD), and zone multipliers — and returns a ranked list with the optimal selection and full cost breakdown.

The agent is designed to be invoked programmatically by the OMS (Order Management System) for each new shipment, replacing the manual comparison step. It also writes a structured audit log of every decision so Sklum can, for the first time, analyze carrier cost variance over time and build the business case for a full TMS investment.

---

## Example Use Cases

1. **Standard mainland Spain parcel (BROWSE replacement)**
   - Input: `"Select carrier for order ORD-8821: 46cm × 32cm × 28cm box, 3.2 kg, destination 28006 Madrid, standard delivery"`
   - Agent calls: `calculate_billable_weight` → `get_eligible_carriers` → `get_all_carrier_quotes` → `log_selection`
   - Output: Ranked carrier list, selects cheapest (e.g. MRW at €6.40), with full cost breakdown

2. **Balearic Islands shipment — remote surcharge detection**
   - Input: `"Route order ORD-9102: 60cm × 40cm × 30cm, 5.8 kg, to 07001 Palma de Mallorca, no special flags"`
   - Agent calls: `calculate_billable_weight` (DIM weight = 14.4 kg > actual) → `get_eligible_carriers` → `get_all_carrier_quotes` (all include Balearics surcharge)
   - Output: Highlights that DHL is cheaper than SEUR for this weight/zone combination despite being a "premium" carrier (rate crossover); selects DHL

3. **Canary Islands COD shipment — complex surcharge stack**
   - Input: `"Assign carrier: 80cm × 50cm × 40cm, 12 kg, to 35001 Las Palmas de Gran Canaria, COD required"`
   - Agent calls: `calculate_billable_weight` (DIM 32 kg > actual 12 kg) → `get_eligible_carriers` (only Correos Express and MRW cover Canaries with COD) → `get_all_carrier_quotes`
   - Output: Applies Canary Islands remote surcharge (€35–55) + COD fee on both eligible carriers; selects cheapest

4. **Oversize furniture piece — dimension threshold check**
   - Input: `"Carrier for ORD-7731: sofa 190cm × 90cm × 85cm, 38 kg, to 08005 Barcelona, residential address"`
   - Agent calls: `calculate_billable_weight` (DIM weight 289.8 kg — triggers oversize flag) → `get_eligible_carriers` (only specialty carriers remain) → `get_all_carrier_quotes`
   - Output: Only 1-2 carriers can handle this; returns only viable options with oversize surcharge applied

5. **Rate crossover detection — express cheaper than economy**
   - Input: `"Route ORD-6610: 15cm × 10cm × 8cm, 0.4 kg actual, to 41001 Sevilla"`
   - Agent calls: `calculate_billable_weight` (DIM 0.24 kg < actual; billable = 0.4 kg) → `get_all_carrier_quotes`
   - Output: GLS Express (€4.20) is cheaper than Nacex Economy (€5.10) for this exact weight+zone combination; selects GLS Express and explains the crossover

---

## Tools Required

| Tool name | What it does | External service | Auth |
|-----------|-------------|-----------------|------|
| `calculate_billable_weight` | Computes max(actual_weight, DIM_weight) where DIM = L×W×H/5000 | None (pure computation) | None |
| `get_eligible_carriers` | Returns OMS-filtered list of carriers covering destination postal code, within weight limits, with required service flags | Mock carrier registry (dict); later: OMS REST API | None / IAM |
| `get_all_carrier_quotes` | For each eligible carrier, computes complete cost (base + per-kg + zone multiplier + fuel surcharge + all applicable surcharges) | Rate card data (dict); later: carrier API or Google Sheets | None |
| `apply_business_rules` | Applies Sklum-specific preferences (carrier avoid lists, preferred carriers per zone, day-of-week restrictions) | Business rules config (dict) | None |
| `log_selection` | Writes the selection decision to an in-memory audit log (later: Google Sheets / BigQuery) including all quotes, selected carrier, and reason | In-memory (prototype); later: Google Sheets API / BigQuery | None / Google OAuth |

---

## Agent Orchestration Pattern

- Pattern: **LlmAgent** (single intelligent agent; deterministic tool calls, LLM provides explanation and handles edge cases)
- State management: **in_memory** (prototype phase)
- The agent does not calculate rates itself — it always delegates to tools. The LLM's role is to interpret order details from natural language, call tools in the correct sequence, explain the selection, and handle ambiguous or incomplete inputs.

---

## Constraints & Safety Rules

- MUST NOT invent carrier rates, surcharges, or availability — all pricing data comes exclusively from `get_all_carrier_quotes`
- MUST NOT select a carrier not returned by `get_eligible_carriers` — eligibility filtering is the OMS's responsibility
- MUST call `calculate_billable_weight` before any rate query — never pass actual weight directly to `get_all_carrier_quotes`
- MUST call `log_selection` for every completed selection — the audit trail is mandatory
- MUST apply `apply_business_rules` after computing quotes and before finalizing selection — business rules can override the cheapest option
- MUST present cost breakdown (base + surcharges + total) for the top 3 carriers, not just the winner
- MUST NOT process shipments with destinations outside Spain or EU without flagging them as out-of-scope for the current rate card
- MUST flag (but not block) shipments where DIM weight exceeds actual weight by more than 3× — these may indicate measurement errors
- MUST NOT expose internal carrier rate card data or fuel surcharge percentages in user-facing responses — show only the final computed total

---

## Success Criteria

| Metric | Threshold | Measurement method |
|--------|-----------|-------------------|
| Tool call accuracy (correct sequence) | ≥ 95% | `tool_trajectory_avg_score` in `adk eval` |
| Carrier selection correctness (cheapest valid carrier selected) | ≥ 90% | LLM-as-judge comparing selected vs ground truth cheapest |
| Rate crossover detection (finds non-obvious cheapest) | ≥ 85% | Specific eval cases with precomputed crossover scenarios |
| Billable weight accuracy | 100% | Unit-tested `calculate_billable_weight` function |
| Audit log completeness | 100% | Assert `log_selection` called on every successful selection |
| Response latency P95 | < 8 seconds | Cloud Trace after Agent Engine deployment |

---

## Edge Cases to Handle

1. **All carriers ineligible** — `get_eligible_carriers` returns empty list (no carrier covers the destination or weight). Agent must respond "no eligible carrier found" and NOT call `get_all_carrier_quotes` or fabricate options.
2. **Business rule overrides cheapest carrier** — `apply_business_rules` marks the cheapest carrier as preferred=false for the destination. Agent must select the next-cheapest and explain why the cheapest was bypassed.
3. **DIM weight triggers oversize flag** — calculated billable weight exceeds 30 kg even though actual weight is 10 kg. Agent must re-run `get_eligible_carriers` with the corrected oversize flag and note the discrepancy.
4. **Incomplete order data** — user provides weight but not dimensions. Agent must ask for missing dimensions before calling `calculate_billable_weight`. Never assume dimensions.
5. **Tie between two carriers at identical total cost** — `get_all_carrier_quotes` returns two carriers with the same total. Agent applies business rules; if still tied, selects the carrier with better historical transit time.
6. **Canary/Ceuta/Melilla destination** — remote area surcharges are high and some carriers don't serve these zones. Agent must correctly identify the zone from postal code and only show carriers with confirmed coverage.

---

## Deployment Target

- [x] **Agent Engine** — managed, registered in Gemini Enterprise via Agent Studio UI
- [ ] Cloud Run + A2A (future phase: when consumed by a multi-agent orchestration layer)

---

## GCP Context

```
Project ID:       yogaproject-1508
Region:           us-central1
Artifact Reg:     will be created by setup-dev-env
Existing MCP:     none (rate cards are in-process Python dicts for prototype)
Existing VPC:     none
```

---

## Spanish Carrier Rate Card Reference (Prototype Mock Data)

### Zone Mapping (by postal code prefix)

| Postal prefix | Zone | Description |
|--------------|------|-------------|
| 01–52 (peninsula) | Z1 | National mainland |
| 07xxx | Z3 | Balearic Islands |
| 35xxx, 38xxx | Z4 | Canary Islands |
| 51xxx | Z5 | Ceuta |
| 52xxx | Z5 | Melilla |
| Non-ES | Z6 | International EU |

### Carriers in Scope (Prototype)

MRW, SEUR, GLS, Correos Express, Nacex, DHL

### Remote Area Surcharges

| Zone | Surcharge |
|------|-----------|
| Balearic Islands (Z3) | €18.00 |
| Canary Islands (Z4) | €42.00 |
| Ceuta / Melilla (Z5) | €55.00 |

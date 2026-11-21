# τ-Banking harness architecture: baseline surface

> **Read [REPORT.md](REPORT.md) first.** It is the current account: what was diagnosed, what the
> harness is now, and the DEV results. Section 5 below describes the v6 gate design, which was
> later switched off.

What the baseline agent operates inside: the loop, the tools, the knowledge base.
Paths are relative to the repo root. Inventory generated from code at `19f13ea3`.

## 1. The baseline harness

```
                ┌──────────────────────────── llm_agent (claude-sonnet-5-5) ──────────────────────────┐
 customer  ◄──► │ system = <instructions> generic rules + <policy> agentic_search.md                  │
 simulator      │ context = full message history (no summarization, no memory across tasks)          │
 (sonnet-5-5,   │ one LLM call per turn → text to customer  OR  tool call(s)                          │
  hidden        └───────────────┬───────────────────────────────┬──────────────────────────────────────┘
  instructions)                 │ shell (read-only, srt)        │ 14 banking tools
                                ▼                               ▼
                     698 KB docs as .md + INDEX.md      TransactionalDB (in-memory, ~25 tables)
                     no truncation, 30 s timeout         unlocks / gives / logged calls are rows too
```

Between the LLM and the environment there is nothing: no planner, no state ledger, no
pre-action check, no retrieval layer beyond the raw shell, no memory. Every "harness"
decision is today implicit in one prompt and the model's own turn-by-turn reasoning.
The adapted harness slots in at the `HalfDuplexAgent` boundary (`src/tau2/agent/`,
registered in `src/tau2/registry.py`).

## 2. Tools

**Initial (14):** `get_current_time` (fixed 2025-11-14 03:40 EST) ·
`get_user_information_by_{id,name,email}` · `log_verification` · `change_user_email` ·
`get_referrals_by_user` · `get_credit_card_{accounts,transactions}_by_user` ·
`transfer_to_human_agents(summary, reason∈enum)` · `list_discoverable_agent_tools` ·
`unlock_discoverable_agent_tool` · `call_discoverable_agent_tool(name, arguments: JSON string)` ·
`give_discoverable_user_tool` · `shell`.

**Discoverable, agent side (44):** found by name in the KB, unlocked, then called.

| kind | tools |
|---|---|
| read (10) | `get_all_user_accounts_by_user_id_3847`, `get_bank_account_transactions_9173`, `get_debit_cards_by_account_id_7823`, `get_debit_dispute_status_7483`, `get_user_dispute_history_7291`, `get_payment_history_6183`, `get_pending_replacement_orders_5765`, `get_closure_reason_history_8293`, `get_credit_limit_increase_history_4829`, `get_atm_deposit_images_8473` |
| write: accounts | `open_bank_account_4821`, `close_bank_account_7392`, `transfer_funds_between_bank_accounts_7291`, `apply_checking_account_credit_5829`, `apply_savings_account_credit_6831`, `submit_interest_discrepancy_report_7294` |
| write: debit cards | `activate_debit_card_8291/8292/8293`, `order_debit_card_5739`, `close_debit_card_4721`, `freeze_debit_card_3892`, `unfreeze_debit_card_3893`, `change_debit_card_pin_6285`, `reset_debit_card_pin_6284`, `clear_debit_card_fraud_alert_4892`, `set_debit_card_recurring_block_7382`, `request_temporary_debit_card_limit_increase_8374`, `file_debit_card_transaction_dispute_6281` |
| write: credit cards | `file_credit_card_transaction_dispute_4829`, `close_credit_card_account_7834`, `log_credit_card_closure_reason_4521`, `order_replacement_credit_card_7291`, `pay_credit_card_from_checking_9182`, `apply_statement_credit_8472`, `apply_credit_card_account_flag_6147`, `submit_credit_limit_increase_request_7392`, `approve_/deny_credit_limit_increase_5847/5848`, `update_transaction_rewards_3847` |
| transfer protocols | `initial_transfer_to_human_agent_0218`, `initial_transfer_to_human_agent_1822`, `emergency_credit_bureau_incident_transfer_1114` |

**Discoverable, customer side (4):** `get_referral_link`, `get_card_last_4_digits`,
`deposit_check_3847`, `submit_cash_back_dispute_0589`. The agent gives one with
`give_discoverable_user_tool`; the customer calls it.
**Customer's own tools:** `apply_for_credit_card`, `submit_referral`,
`request_human_agent_transfer`, `submit_transaction`.

Traps in the tool surface, from the inventory:
- **Selection among near-duplicates.** The three `activate_debit_card_829x` differ only by
  `issue_reason` (new/first, lost/stolen/fraud, expired/damaged/upgrade/reissue). The two
  `initial_transfer_to_human_agent_*` share an identical docstring; which one applies is in the KB.
- **Decoys and dead names.** `example_agent_tool_0000` is in no doc. `downgrade_credit_card_3847`
  is named in 3 docs but not implemented.
- **Unlocks are state.** Unlocking "to look", giving the wrong user tool, or making an extra
  logged call changes the DB hash.
- **No unlock enforcement on raw names** *(checked)*. The environment runs a discoverable tool
  called by its raw name, skipping the unlock and the log row.

## 3. Knowledge base

698 docs, about 195K tokens, about 817K chars. Each is `{id, title, content}` (Markdown with tables),
exported to the sandbox as `<id>.md` plus `INDEX.md` (one line per doc: file and title).

| area | docs |
|---|---|
| checking accounts | 110 |
| credit cards | 110 |
| savings accounts | 89 |
| business savings / checking / credit | 82 / 79 / 79 |
| EveryonePay (P2P) | 51 |
| buy-now-pay-later | 48 |
| bank accounts (general) | 47 |
| other | 3 |

Structure relevant to the hypotheses (counts, not yet causes):
- **Tools are needles.** 37 of the 48 discoverable tools are named in exactly one doc, and none in more
  than four. Finding the procedure doc is a precondition for acting at all.
- **Procedures rarely chain tools in one doc.** Only 12 docs name more than one discoverable tool.
  Multi-step tasks must assemble their order across docs (H3), and the governing rules
  (eligibility, fees, limits, exceptions) live in product docs separate from the procedure
  doc that names the tool (H1).
- 117/698 docs contain an explicit cross-reference phrase ("see", "refer to", "as outlined in").
  This is a lower bound on the dependency structure: most dependencies are implicit (same
  product, same entity) rather than linked.

## 4. Profile of the baseline failures

See `FAILURE-PROFILE.md`. In short, retrieval and tool selection work. Failures cluster at:
- decision points: transfers, prerequisites before writes, combining rules from several docs;
- per-item state;
- conflicts the KB does not resolve.

## 5. Adapted harness v6 (`--agent adapted_agent`)

Code: `src/tau2/agent/adapted/`. Offline artifacts: `adapted-harness/kb_index/`.
Run: `adapted-harness/run_adapted.sh`. The environment keeps the pinned `terminal_use` setting;
the orchestrator, environment, tools, user simulator and evaluator are unchanged. Everything
sits behind the `HalfDuplexAgent` boundary.

**Design rule (no overfitting):** every v6 component is a general mechanism, applied to every
tool and task the same way, and built from the KB alone. Hand-curated knowledge found by
comparing against DEV gold (rule cards, the account_class rule) is off by default and kept
only as an ablation.

```
 customer ─► ContextBuilder.incoming ────────────────────────────────────────┐
             · grounding note: open ledger items + open procedure steps       │
             · shell output → docs the model has read (quote checks use this) │
             · unlock result + docs that name the tool                        │
                                                                              ▼
 system prompt = policy + <harness> protocol + <cross_document_reasoning> + <retrieval>
                                                                              │
                         ┌────────────── LLM (claude-sonnet-5-5) ◄────────────┘
                         ▼
   retrieval, one pipeline:  FIND kb_search (BM25, snippets) → CONNECT kb_related (index)
                             → READ shell cat/grep (pinned env tool) → QUOTE in precheck
   harness tools (answered inside the agent, never reach the env):
     kb_search · kb_related · update_ledger · precheck ── Gate.check:
        ├ contract prerequisites done                     (tool contracts, 30 tools)
        ├ quotes match text the model saw
        ├ preconditions met, or customer_attested after a lookup that cannot cover it
        ├ derived argument values justified
        ├ cross_doc_check for ≥2 cited docs; conflicts resolved or stated as open
        ├ earlier procedure steps done or n/a with reason  (workflows, 55 procedure docs)
        ├ every known issue for this tool addressed       (180 issues, 30 tools)
        └ transfer: consent, policy rule 6 (4 asks) or KB rule, no open requests
                         ▼
   Gate.screen: a state-changing call runs only if it matches a passed precheck
                         ▼
 environment ◄── real tool calls (unchanged tools, unchanged grading)
```

### Components, the gap each closes, and evidence

| Component | Module | Gap it closes | Evidence so far (single runs) |
|---|---|---|---|
| Precheck gate on writes, gives, transfers, email change | `gate.py` | C1: no check before acting | 087 stopped escalating early (v1) |
| Transfer rule (policy rule 6, consent, no open requests) | `gate.py` | transfer as an escape hatch | **081 fixed** (v2), held in v5 |
| KB tool contracts (required lookups per write tool) | `kb.py`, `build_contracts.py` | prerequisites only in prose | 078 no longer closes a card with pending transactions |
| Ledger + grounding note | `context.py` | C2: decisions follow the latest customer message | protocol-driven; **099 fixed** (v2) |
| Derived-argument provenance + `customer_attested` | `gate.py` | wrong value sources; over-verification | 028 regression traced to the old rule and fixed; not yet re-run |
| Cross-document check | `prompts.py`, `gate.py` | 7/267 prechecks recorded a conflict before | v5: 28/47 prechecks filled `cross_doc_check` |
| Procedure to-do list (workflows) | `context.py`, `gate.py` | H3: implicit step order across docs | new in v6 |
| Known-issues checklist | `kb.py`, `gate.py` | conflicts and ambiguities hit at decision time | new in v6; recovered every conflict found by hand (082/084/087 dispute fields, 078 status dependency, 066 naming) from the KB alone |
| Open-issue decision rule | `prompts.py` | guessing when the KB is silent | new in v6: ask for customer-only facts, else follow the procedure literally and record the assumption |
| Hybrid retrieval: `kb_search` + `kb_related` + shell | `kb.py` | needle-in-698-docs search; implicit links | BM25 alone 5% recall on customer text; +index 1-hop 15% (offline); live `kb_related` returns 59% required docs (v5) |

### Offline knowledge artifacts (built from the KB only; no task, gold or DB data)

| Artifact | Builder | Content |
|---|---|---|
| `out/contracts.json` | `build_contracts.py` | 30 write tools: prerequisite lookups, conditions, ordering, rule-set arguments |
| `out/workflows.json` | `build_workflows_issues.py` | 55 procedure docs: ordered steps with tools |
| `out/known_issues.json` | `build_workflows_issues.py` | 180 issues across 30 tools (79 ambiguity, 71 cross-doc dependency, 30 conflict); 70 resolved by the KB |
| `out/index_proc90.json` | `build_index.py` | 90 procedure/general docs: needs matched to providing docs (default) |
| `out/index_all698.json` | `build_index.py` | full KB; lower precision (8% vs 14% offline), kept as an artifact |
| `rule_cards.json`, `arg_rules.json` | hand-curated | DEV-informed; **off by default** (ablation only) |

All quotes in every artifact are checked against the cited document; failing entries are dropped.

### Configuration

One `HarnessConfig` (`config.py`), read from `HARNESS_*` variables; the factory logs it. Each
component can be switched off for an ablation: `HARNESS_GATE`, `HARNESS_LEDGER`,
`HARNESS_DERIVED`, `HARNESS_CONTRACTS`, `HARNESS_CONFLICTS`, `HARNESS_WORKFLOWS`,
`HARNESS_ISSUES`, `HARNESS_INDEX`, `HARNESS_KBSEARCH`; ablation-only knowledge:
`HARNESS_RULECARDS=1`, `HARNESS_ARGRULES=1`. Retrieval: `HARNESS_RETRIEVAL` (default
`terminal_use`, the pinned setting).

### Information boundary

The harness reads only what the agent could see: its tool results, the KB, the policy. The
`task` passed to agent factories is ignored. Grader data was used only for diagnosis
(`adapted-harness/diagnostics/`) and to *score* retrieval and the index, never as agent input.
Which components exist was chosen from DEV failures, so DEV scores are optimistic: only the
frozen TEST split measures generalization.

### Known limits

- **Discretionary provisional credit** (082, 084): doc 032 has three outcomes, the tool takes a
  boolean, and gold's choice is not derivable from the KB.
- **Gold issues:** 070/071 (formation date nobody knows) and 083 (gold replay errors).
- **Cost:** v5 was about $7.50 per task against $2.10 for the baseline; v6 adds checklist items.
- **Retrieval ablation:** `bm25_grep` (τ²'s KB_search + grep instead of the shell) gave the
  baseline the same SMOKE score (3/6) as `terminal_use`.

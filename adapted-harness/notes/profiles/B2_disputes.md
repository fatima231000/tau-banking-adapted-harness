# B2: debit-card transactions and disputes (DEV run, sonnet-5-5, terminal_use)

Tasks: task_078, task_082, task_083, task_084. All four score reward 0. Sources: the DEV traces, `adapted-harness/diagnostics/out/dev-baseline.dbdiff.md`, the task JSONs, `results.json` (for the full dispute argument strings and timestamps), KB docs 025/031/032/033, and `tools.py:940` (the dispute tool signature).

Note: task_078 is a lost-card replacement task. It has no dispute, but it shares the transaction tool.

---

## task_078 (DB): lost wallet, 3 debit cards

**Outcome.** The customer wanted all three cards frozen, then closed and replaced. Gold freezes all three, pulls transactions on all three accounts, then closes only Light Blue and Green. It leaves Light Green FROZEN because that account has 2 pending transactions (btxn_9034c8e42248, btxn_3e4b057911a1). It then orders the Green replacement, EXPEDITED, $15. The agent got everything else right but closed Light Green too [52]. It never unlocked or called `get_bank_account_transactions_9173`.

**First divergence: [40]/[42].** The customer confirmed the cards were lost [39], and the agent went straight to `close_debit_card_4721` on all three cards without checking transactions.

**Docs.** The agent read doc 025 at [5], and doc 025 contains the rule. Required docs 018 (transactions) and 005 were partly read later. 018 was never opened in this task.

**Root cause.** R4 primary: a prerequisite check was skipped. Doc 025 lists requirement 4: "No pending transactions: The card must not have any pending or processing transactions… must wait for all transactions to settle before the card can be closed." The secondary cause is a conflict inside the same document (R9). Step 4 of doc 025 for lost/stolen cards says "Inform customer that any pending transactions will still be processed", and the agent repeated that framing at [30] and [56]. It seems to have read lost-card closure as exempt. The doc says the exemption covers only requirement 6, the card age.

**Against.** No evidence against: the agent had the doc and the tool name, and the task was not hard.

**Harness fix.** A pre-action eligibility checklist for write tools. Before `close_*`, list every numbered requirement in the governing doc and show the tool call that satisfies each one.

---

## task_082 (DB): 4 disputes on 2 cards (Marcus Chen), 875 s

**Outcome.** The agent filed all 4 disputes with the right transactions, categories, types and card_action values. It closed the Blue card and ordered its replacement exactly as gold does, and the set of unlocked tools matches gold. The DB diff differs from gold in three areas:

| Dispute | Field | Agent → gold | KB rule that sets it |
|---|---|---|---|
| ElectroniX $347.50 (card_present_fraud) | pin_compromised | yes_observed → yes_shared | 031 §11. The customer kept the PIN on a sticky note in the wallet [40]. Neither option fits cleanly. |
| ElectroniX | provisional_credit_eligible | true → false | 032: "NOT REQUIRED … Customer shared their PIN voluntarily (pin_compromised = 'yes_shared')". Follows from the PIN field. |
| ElectroniX | customer_max_liability_amount | 347.5 → 50 | 031/036 liability tiers (see the mechanism section) |
| FitLife $89.99 (recurring) | card_in_possession, pin_compromised | false, yes_observed → true, no | The customer said explicitly at [53]: "I still had the card when FitLife charged me… no PIN involved". |
| FitLife | provisional_credit_eligible | false → true | The agent's value follows 032, which lists recurring_charge_after_cancellation as NOT REQUIRED. **Gold contradicts the KB here.** |
| FitLife / ATM / CryptoGems | customer_max_liability_amount | 89.99 / 100 / 500 → 50 / 50 / 50 | Liability tiers |
| GFF card | status | CLOSED → ACTIVE | 031: card_not_present_fraud → close_and_reissue, and "the agent must separately perform the indicated card action". The customer asked for it to be closed [68]. **The agent follows the KB; gold does not.** |

**First divergence: [44].** The first dispute was filed with liability 347.5 and PIN yes_observed. At [52] the agent explained it as "Reg E would cap it at $500 because you're reporting within 60 days". The charge was 7 days old and found that day.

**Docs.** The agent read 031–037, 018, 009, 028, 029, 030, 023 and 025, which covers every required doc.

**Root cause.** R9 primary: the KB does not say what the liability tier is measured from. It says "of statement", and the DB has no statement dates. This wrong field appears in 4 of 4 disputes. Secondary R5: at [54] the agent carried card-level facts (card lost, PIN compromised) into a dispute whose charge predates the loss, against what the customer had just said. There is also an R8 part: gold contradicts the KB on the FitLife provisional credit and the GFF closure, so even a KB-perfect run fails this task.

**Harness fix.** A per-dispute fact sheet, re-asked or confirmed for each transaction. Also a label audit of the gold.

---

## task_083 (ACTION): 4 disputes, PIN shared with nephew (Diana Kowalski)

**Outcome.** The agent filed all 4 disputes in one batch [44], and the categories, types and card_action values all match gold. It then froze the GFF card per the 031 most-severe rule [51]. When the customer asked for a new number [60], it unfroze and closed the card [64]–[66]. All 5 gold unlocks are OK, and all 4 dispute calls are MISS.

**Grader artifact (this alone makes the task unpassable).**
- Gold's dispute calls leave out `customer_max_liability_amount`, but that is a **required positional parameter** in `tools.py:940` (`customer_max_liability_amount: float`, no default). Replaying gold returns `Error: Invalid arguments: missing…`. That is why the DB diff lists all 4 agent disputes as "EXTRA in agent run": the gold DB has none.
- `compare_with_tool_call` compares the nested `arguments` string byte for byte. Gold writes `"disputed_amount": 150.00` with `", "` separators. The agent wrote compact JSON with `150.0`.
- So no call can both succeed and match gold. Dispute 1 (ATM) and dispute 2 (frames) differ from gold **only** by this artifact.

**Real behavioral differences, setting the artifact aside.**
- **Duplicate coffee $67.25**: the agent recorded `pin_compromised: yes_shared` against gold's `no`, and provisional credit false against gold's true. The customer's PIN answer was given per card at [40] ("Green, yes. I shared it"). The agent applied it to a signature-purchase duplicate charge, and the customer objected at [54]. At [59] the agent named the 032 clause "Customer has not contacted merchant first (for non-fraud disputes)" as the deciding factor. That clause conflicts with 032's REQUIRED list, which includes duplicate_charge. Gold gives the REQUIRED list precedence.
- **GameStop**: the agent disputed $425 against gold's $475. The customer had authorized $50. Disputing only the unauthorized excess is defensible, and gold itself disputes only the $150 shortfall on the ATM charge.
- **Extra liability values** (150 / 189.5 / 50 / 50): the parameter is required, so the agent had to supply them. Gold has no values to compare against. The agent's rule was min(disputed amount, tier cap), with the tier counted from the discovery date. That rule is internally consistent.

**Root cause.** R8 primary (gold calls a tool without a required parameter, plus byte comparison). R5 secondary (the PIN answer was carried over to the duplicate dispute).

**Harness fix.** None for the score: fix the gold, or compare the parsed JSON for the fields gold specifies. For behavior, the same per-dispute fact sheet as in 082.

---

## task_084 (DB): 4 disputes, Entry-tier dispute limit (Valeria Montes), 831 s

**Outcome.** The agent handled the hard parts correctly:
- It found the existing open dispute and applied the Entry Tier limit of 2.
- It let the customer choose TechWorld, the earliest duplicate, and the $100 incorrect-amount difference.
- It filed card_present_fraud with liability 412.88, which **matches gold**.
- It closed the card without ordering a replacement, respecting the 48-hour wait.

Only two dispute rows differ from gold:

| Dispute | Field | Agent → gold | Rule |
|---|---|---|---|
| Bella's duplicate $47.50 | provisional_credit_eligible | false → true | 032 conflict. The agent applied "not contacted merchant → NOT REQUIRED" ([35], explained to the customer and accepted). Gold applies the REQUIRED category list. |
| Bella's duplicate | customer_max_liability_amount | 47.5 → 50 | Liability tiers. Gold's 50 is larger than the disputed $47.50, which contradicts the tool's own docstring: "based on … reporting timing rules **and the disputed amount**". |
| Whole Foods incorrect $100 | customer_max_liability_amount | 100 → 50 | Liability tiers |

**First divergence: [35].** The agent decided, out loud, that the duplicate was not eligible for provisional credit because the customer had not contacted the merchant.

**Docs.** The agent read every required doc (031–035, 018, 028, 009, 025, 029, 023, 030).

**Root cause.** R9 primary: two KB rules are underspecified or in conflict, the liability anchor and 032's REQUIRED vs NOT-REQUIRED overlap. R8 secondary: gold's 50 on a $47.50 dispute.

**Against.** If the 032 lists are read as "category list overrides", the agent misread a rule (R2 within one doc). That reading is available, but the text does not state it.

**Harness fix.** An explicit decision table for provisional credit and liability, stating the precedence and the date the clock starts from, given to the agent as a reference. Without a KB or gold fix, the liability field cannot be learned reliably.

---

## Why 082 and 084 took 800+ seconds: infrastructure, not deliberation

The two runs overlapped in wall-clock time (082 ran 14:44:15–15:12:10, 084 ran 14:45:27–15:12:38). Both show stalls in **the same windows**:

| Window | 082 | 084 |
|---|---|---|
| ~14:47 → 14:56 (~9 min) | Before msg 64, which is a *customer* turn of 471 tokens | Before msg 37, an agent turn of 306 tokens (539 s gap) |
| 14:56:3x → 15:12:0x (~15.5 min) | Before msg 71, 848 tokens | Before msg 49, 1123 tokens (939 s gap) |

The stalled turns are small and hit both the customer simulator and the agent. That points to a provider-side stall or rate-limit backoff shared by the concurrent run, not to reasoning time. Without the stalls, each run took about 4–5 minutes. Duration figures from this run should not be read as agent effort.

---

## Do they share one mechanism?

**Partly.** In 082, 083 and 084 the failure lives in a few **derived dispute fields**. The model found every required doc, and the transactions, categories, types, card_action values and ordering are almost entirely right. Three sub-mechanisms stack:

1. **The KB does not pin down the liability rule (082, 084; forced into 083).** The tier is measured "of statement", and the DB has no statement data. The tool asks for an amount that depends on "timing … and the disputed amount". Gold appears to use $50 for any November charge, as if no statement had been issued yet, whatever the amount: 50 even on $47.50. It uses min(amount, $500) only for the October charge (412.88). The agent's starting date drifts between transaction date and discovery date, and it applies min(amount, cap). This field alone fails 6 of the 7 graded dispute rows in 082/084.
2. **Overlapping provisional-credit clauses in 032 (083, 084).** The REQUIRED-categories list overlaps with the "not contacted merchant → NOT REQUIRED" clause, and the doc does not say which wins.
3. **Per-card facts reused across disputes (082 FitLife, 083 coffee).** The agent applied one card's PIN or possession status to every dispute on that card, even when the customer said otherwise. This is the one clear agent error that a harness could fix.

On top of these, **gold is internally inconsistent** in a way that blocks a KB-faithful agent:
- 082: provisional credit on the recurring charge, and the GFF card left active.
- 083: gold omits a required argument and never performs the freeze action.
- 084: liability 50 on a $47.50 dispute.

task_078 has a different mechanism: an eligibility check was skipped before a write (R4).

H1/H2/H3 mostly **do not fit** these tasks. There is no customer over-trust (H2). The cross-doc combination (H1) was done correctly: for example 031 card mapping with 029/023 replacement rules, and 033 ATM handling. Only 078 fits H3.

**Governing KB passages:**

- doc 031: "Reported within 2 business days of statement: Maximum liability $50 / Reported within 60 days of statement: Maximum liability $500 / Reported after 60 days: Unlimited liability"
- tool docstring: "customer_max_liability_amount (number): The maximum dollar amount the customer could be liable for based on Regulation E reporting timing rules and the disputed amount. Use -1 for unlimited liability."
- doc 032: "Provisional Credit is REQUIRED when ALL of these conditions are met: … 2. Dispute Category: … 'unauthorized_transaction', 'card_present_fraud', 'card_not_present_fraud', 'atm_cash_discrepancy', 'duplicate_charge' … Provisional Credit is NOT REQUIRED … when: 1. The dispute category is: 'goods_services_not_received', 'recurring_charge_after_cancellation', 'atm_deposit_not_credited', 'incorrect_amount' 2. Customer has not contacted merchant first (for non-fraud disputes) 3. Customer shared their PIN voluntarily (pin_compromised = 'yes_shared')"
- doc 031: "Note: This parameter records metadata only; the agent must separately perform the indicated card action after filing the dispute." The gold for 082 and 083 does not follow this.
- doc 025 (for 078): "4. No pending transactions: The card must not have any pending or processing transactions. If pending transactions exist, inform the customer they must wait for all transactions to settle before the card can be closed."

---

## 3-line summary

1. 082, 083 and 084 fail on a handful of derived dispute fields, not on retrieval or ordering. The main one is `customer_max_liability_amount`, which the KB does not pin down; the others are 032's overlapping provisional-credit clauses and per-card facts reused across disputes.
2. task_083 cannot be passed: gold omits a required parameter, so replaying it errors, and the arguments are compared byte for byte. Gold for 082 and 084 also contradicts the KB in places (recurring provisional credit, GFF card not closed, $50 liability on a $47.50 dispute). These tasks need a label audit before any harness change is judged on them.
3. task_078 is a plain skipped prerequisite: no transaction check for pending charges before closing a card. The 800+ second runs (082, 084) come from shared provider stalls at the same times, not from agent deliberation.

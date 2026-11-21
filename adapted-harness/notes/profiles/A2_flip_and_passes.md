# A2: task_087 flip (DEV fail, SMOKE pass) and profile of SMOKE passes

Sources: DEV = `adapted-harness/baseline/dev-sonnet55-terminal/traces/task_087.md`; SMOKE = `data/simulations/smoke-baseline-sonnet55-terminal/traces/<task>.md`; task JSONs; KB docs `doc_bank_accounts_bank_accounts_(general)_{025,031,039}`, `doc_checking_accounts_checking_accounts_(general)_003`; `prompts/components/policy_header.md`.

## Part 1: task_087 paired comparison

**Outcome.** The customer has three cards declining with CODE 05. Gold: unfreeze Blue and clear its velocity block; unfreeze Green; on Evergreen, pull transactions, file a fraud dispute for the $499.99 TechZone charge, close the card (fraud_suspected) and order a free expedited premium replacement. DEV got everything up to Evergreen right (11/11 OK lines), then transferred to a human. That left 4 tool calls plus the dispute, closure, order and new-card rows missing (dbdiff lines 65-72). SMOKE did all of it.

**The two runs match through the Evergreen diagnosis.** Both ran the same greps at [3]/[5] and read docs 028, 039 and 026 at [18]. Both made the same verification call and the same three card lookups at [27], and sent near-identical summaries at [31]. Neither run ever pulled Evergreen transactions before asking the customer to confirm them (DEV [31]/[47], SMOKE [31]/[40]).

**Decisive fork: the customer's Evergreen turn (DEV [48] vs SMOKE [41]), then the agent's next action.**
- DEV customer [48] told the alert story: "suspicious charge, around $500 ... I was definitely in Seattle ... Can you remove it now?" It gave no itemized review. The agent went straight to `transfer_to_human_agents` at [49]. It ran no transaction lookup, opened no dispute doc, and did not ask the customer before transferring.
- SMOKE customer [41] told the same story and added an itemized review: "Whole Foods was me ... Netflix is my subscription. But that $500 charge ... definitely wasn't me." The agent opened doc 031 (dispute) and doc 018 at [42], pulled transactions at [49], and continued down the dispute, close and reorder chain (docs 025, 023, 029).

**Agent or customer?** The difference in the customer's turn set it off, but the agent made the decision.
- *The simulator did vary.* At DEV [47] the agent explicitly asked the customer to confirm the transactions. That should have triggered the customer's script step 12, the itemized denial, but the DEV customer answered only with step 11. In SMOKE the customer merged steps 11 and 12. It even quoted amounts the agent had never shown it, which is leakage from its own script.
- *That variation did not make success impossible (not R7).* DEV [48] still plainly reported an unauthorized ~$500 charge. Doc 031 covers exactly that case ("unauthorized charges"). The policy header says to transfer "only if ... you are sure that there are no potential actions you can take as specified in the knowledge base" and "Do not transfer without asking the user first." DEV broke both rules.
- *Why DEV went wrong.* Doc 039, which DEV did read, says "Escalate to security team when: ... Customer reports transactions they did not make." The agent treated this clause as final. Doc 031's title, "Internal: Filing a Debit Card Transaction Dispute", was visible in DEV's INDEX grep at [17], but DEV never opened it.

**Code: primary R1 (retrieval-miss).** DEV stopped searching once it found an escalation clause and never opened the governing dispute doc 031. **Secondary R6 (premature end):** it transferred without asking the customer, leaving 3 of the 4 Evergreen steps undone.

**Evidence against.** Doc 039's escalation clause literally supports DEV's transfer. The KB itself conflicts here: 039 says escalate, 031/025/023 say dispute, close and reissue. Read that way, the root cause is R2-like (doc precedence), with part of the blame on the KB or task design. Also, SMOKE never resolved that conflict either. It simply never re-read 039's escalation clause after the customer's denial. Its pass came partly from the customer's more explicit wording.

**Harness fix (plausible).**
- A pre-transfer gate: before `transfer_to_human_agents`, require a KB search for an in-scope action on the reported issue (e.g. "unauthorized charge" → dispute doc), and require explicit consent from the customer.
- A fetch-before-asking rule: pull the record (here, transactions) before asking the customer to vouch for it.
- A doc-dependency map linking 039's escalation rule to 031, 025 and 023.

## Part 2: SMOKE passes

### task_024 (business card for a $40k truck; graded on the customer's `apply_for_credit_card`)
- **Procedure:** information only, no verification needed. Ran `get_current_time` [9] to check promo dates. Recommended one card with worked arithmetic [11], then confirmed the customer's own summary of the maths [13].
- **KB search:** 3 shell calls. `ls; cat INDEX.md; grep -ril business` [3], then two batch `for f in ...; cat` loops [5][7] that opened **30 docs**: Bronze, Gold, Platinum, Silver, Silver Zoom and Green families. All 6 required docs were opened (Bronze 001/002/010, Silver 001/002/012). The unopened promo docs (Platinum 008/012, Gold 010, Silver Zoom 011) are annual-fee or referral docs that do not change the ranking.
- **Reasoning:** reasoned explicitly that a truck earns only the base rate. Bronze: $400 cash back plus a $500 statement credit = $900. Silver: 2x promo = $800, and the promo ends 2025-11-14 per Silver 012. Platinum: $600. It flagged the credit-line risk (Bronze line $10k-$50k may not cover $40k).
- **Tools:** no discoverable tools. The customer's first apply failed on the card_type string [15] and the customer retried on its own [17], which was outside the agent's control.
- **Lucky?** No. The ranking is robust to the docs it skipped.

### task_057 (choose and open a checking account, refuse an early savings account, give the check-deposit tool)
- **Procedure:** read doc 001 (the opening procedure) [5] before asking for verification. Then `get_user_information_by_name` → `get_current_time` → `log_verification` [9-12], followed by an eligibility lookup (`get_all_user_accounts`) [17] before recommending anything. It narrowed accounts one criterion at a time as the customer revealed them: no overdraft fee [23-29] → overdraft-protection transfer [31-39] → early direct deposit [41-47] → fee waiver at $625 [49-51] → eco/premium red herrings [53-60].
- **KB search:** 22 shell calls, and the work is mostly `grep -H` across the `doc_checking_accounts_*` family before targeted `cat`s. It opened about 45 docs, many truncated with `cut -c`. All 5 required docs were opened (001, 002, 009, 011, Blue 001).
- **Verification and tenure:** the customer falsely claimed "it's been 14 days now" [75]. The agent re-called `get_current_time` [76] and refused again [78]. It also re-queried the accounts [72] to check tenure rather than trusting its memory.
- **Discoverable tools:**
  - It grepped `open_bank_account_4821` [62] before unlocking it, and every unlock was used.
  - It read doc 011 before `give_discoverable_user_tool` [82].
  - The give included an extra `arguments` field. The grader marks that line MISS, but DB grading passed. This would fail an ACTION-graded task.
  - When the customer called the wrong tool name [86], the agent restated the exact name [88]. It then confirmed the deposit by re-querying the account [92].
- **Lucky?** Mostly no.
  - The first recommendation (Light Blue [39]) was premature but correctly revised once the early-deposit criterion appeared.
  - It excluded Evergreen, Bluest, Gold Years and Purple only on "can't confirm overdraft terms". That holds: grep confirms none of those docs mention overdraft. So the inference was sound, though it rested on absence of evidence.

### task_072 (ATM fee errors across two accounts; net credit per account)
- **Procedure:** read doc 017 (the credits policy) [5] before anything else, including its one-credit-per-account rule. It then verified identity [9-13] and pulled the accounts [19] and both accounts' transactions [21]. It cross-checked against the fee docs [21][26] and computed the full net correction before one write per account [30]: Bluest $14.00 and Light Green $3.50, both `fee_refund`, the majority type under doc 017.
- **KB search:** 6 shell calls. One upfront `cat` of 017/019/018/Bluest 010/Light Green 013. Then `cat ... | grep -B3 -A10 "atm|rebate"` across all Bluest and Light Green docs, then targeted cats of Bluest 001/003/007 and Light Green 001/009. All 9 required docs were opened.
- **Reasoning:** it caught all 8 seeded errors, including the net-zero Light Green domestic case: fee charged on the wrong withdrawal, but the total is correct [33].
- **Tools:** 3 unlocks, all used. It made no exploratory writes.
- **Lucky?** No. Every amount matches gold and the reasoning is itemized. It credited the accounts before telling the customer. Doc 017 step 6 ("inform the customer" after applying) permits this.

### Reliable strengths (each backed by trace evidence)
- **Verification is clean and done once.** It looks the customer up by name, gets the time, and logs verification with every field taken from the DB record, before any account tool (057 [9-12], 072 [9-13], both 087 runs). With two same-name users it picked the right one by matching the identifiers (087 DEV [12-15]).
- **It reads the procedure doc before writing.** Doc 001 came before the account opening (057 [5]), 011 before the tool give (057 [80]), 017 before the credit (072 [5]), and 031/025/023 before the dispute, closure and order (SMOKE 087 [42][62][65]). The one run that skipped this, DEV 087, failed.
- **Unlocks are grounded and minimal.** It greps the exact tool name in the KB before unlocking (057 [62], 087 [20]) and never unlocks a tool it does not use. JSON-string arguments were correct on the first try in every write call it made.
- **It checks claims against the system clock and DB.** It refused the false "14 days now" claim via `get_current_time` (057 [76]). It re-queried accounts for tenure and deposit confirmation (057 [72][92]).
- **It does exact multi-item arithmetic under one-shot constraints.** All 8 fee errors were netted into 2 credits (072 [30]). It ran a five-card return comparison with the promo dates checked (024 [11]).
- **It uses the shell for broad, parallel search.** Batch `for f in ...; cat` loops (024 [5][7]) and `grep -H` across a whole doc family (057 [25][41][49]) get high coverage of the required docs (6/6, 5/5, 9/9) in few calls.

### Passes that look lucky
- **SMOKE task_087 (partly).** Its pass depended on the customer volunteering an itemized denial, with amounts the agent had never shown it. The agent's reasoning never resolved doc 039's "escalate when customer reports transactions they did not make". It also asked the customer to confirm transactions before pulling them, the same latent weakness as DEV.
- **task_024 (mild dependence on the simulator).** The graded write is the customer's own tool call, and it succeeded only after the customer fixed its own card_type error.
- **task_057 (grader leniency).** The give call with an extra `arguments` field passed only because the grading here is DB-based, not action-based.

## Summary
1. **The task_087 flip came from the agent, set off by the customer.** Both runs were identical through the card diagnosis. Given a less explicit (but still clear) fraud report, DEV took doc 039's escalation clause, transferred without asking, and never opened the dispute doc 031 (R1 + R6, with a real KB conflict as mitigation).
2. **The agent is strong at the mechanics:** clean verification, grounded and minimal unlocks, correct JSON arguments, exact arithmetic, and checking claims against the clock and DB. Passes come when it reads the governing "Internal:" procedure doc before acting.
3. **Shared weakness across pass and fail:** it asks the customer to vouch for data it has not pulled, and it ends a search at the first rule that applies. A fetch-before-asking rule plus a pre-transfer/pre-terminal-action KB gate is the most plausible harness change.

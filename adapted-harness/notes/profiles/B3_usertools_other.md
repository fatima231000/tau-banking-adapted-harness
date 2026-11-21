# B3: user-tool and other failures (DEV run, dev-sonnet55-terminal): task_015, task_026, task_099

Sources: DEV traces under `adapted-harness/baseline/dev-sonnet55-terminal/traces/`, `adapted-harness/diagnostics/out/dev-baseline.dbdiff.md`, task JSONs, KB docs. None of the three tasks has a SMOKE trace or a smoke dbdiff entry.

## task_015: Platinum referral link never handed over

**Outcome.** The customer asked about five card referral offers and only the last (Platinum Rewards) was correct. Gold gives `get_referral_link` without verifying the customer, and the customer calls it. The agent rejected the first four correctly ([15], [21], [25], [29]). At [33] it confirmed Platinum matched, then made verification a condition of giving the tool. The customer had only a user ID and phone number, so the agent transferred to a human at [41]. In the DB diff, the referral record, the given tool and the tool call are all MISSING.

**First divergence.** [33]: "Before I give you the referral link tool, I need to check your referral history… That check requires me to verify your identity first."

**Docs.** It read the governing doc `credit_cards_(general)_009` [10], plus `_002`, `ecocard_011`, `business_gold_010`, `silver_zoom_011` and `platinum_008`. Retrieval was complete.

**Root cause.** Primary R9: a gate the agent imposed on itself (over-verification). Doc 009 tells the agent to withhold the tool only "if there is reason to believe the referral will be automatically rejected". Nothing gave such a reason here. Policy says: "You should ONLY verify a user's identity if you need to access or modify their customer information." Giving the tool needs neither. Secondary: the transfer at [41] followed from the gate.

**Against.** Doc 002 says "Track the timing of your last two successful referral bonuses before sending additional referrals". That can be read as licence to check history, so the gate was defensible. Gold just never exercises it. This is partly a task-design ambiguity.

**Harness fix.** A pre-action check: "Is a DB read actually required by the doc, or only by caution?" A verification-necessity rule tied to the policy's ONLY clause.

## task_026: dispute and correction flow stopped halfway

**Outcome.** Gold disputes four mis-rewarded transactions: three under-rewarded, plus GitHub `txn_b7e2d4c5f506`, which was over-rewarded at 10% instead of 4%. After the disputes resolve, gold unlocks `update_transaction_rewards_3847` and rewrites all four. The agent disputed only the three under-rewards ([25]–[34]). Then it said it had no update capability ([39], [41]) and transferred to a human ([43]). The DB diff has 4 `rewards_earned` DIFFs, plus the GitHub dispute and call MISSING, plus the unlock MISSING. The `give` MISS line is only how the grader displays it: the agent passed an extra `arguments` field, but the given tool is in the DB.

**First divergence.** [30]: "A dispute only applies when you believe you received too little." That is not in doc 003, which says "a discrepancy between the cash back they received… and the cash back they should have received". Then at [41]: "I can't find any process in my knowledge base", said with **no search after [35]**.

**Docs.** It read `credit_cards_(general)_003` [18] and the rate docs. It **never opened `credit_cards_(general)_004`** ("Applying Resolved Cash Back Dispute Corrections"), which is listed in INDEX. Its only grep [15] (`discrepan|rewards review|…`) missed it.

**Root cause.** Primary R1: retrieval miss on doc 004. The agent did no retrieval for the Phase-2 request and claimed the capability was absent. Secondary R9: it narrowed "discrepancy" to under-rewards only.

**Against.** The agent's rate arithmetic was right, and its view of over-rewards is a plausible customer-service intuition. Still, doc 004 was one `grep dispute` away.

**Harness fix.** Before the agent says "no tool or process exists", require a KB search keyed on the new request (resolved, dispute, update). A sub-task ledger would also keep the post-dispute correction step on the list.

## task_099: correct answer, prerequisite lookup skipped

**Outcome.** The customer wanted the referral with the biggest referrer bonus for a $30k deposit. The agent verified him, pulled referrals, and correctly recommended World Blue at $300 [18]. The customer submitted the World Blue referral [20]. The only DB diff is that the `get_all_user_accounts_by_user_id_3847` unlock and call are MISSING. The run is not a premature end: at 21 messages it is short because it was efficient, and the customer ends with ###STOP### after a successful submit.

**First divergence.** [11]: to check eligibility the agent called `get_credit_card_accounts_by_user`, the wrong store, and not the bank-accounts tool. At [18] it then declared "you're eligible to submit referrals" without checking how long he had held a checking account.

**Docs.** It read `_047` and `_048` [5] and all eight product referral docs, including `world_blue_001` [15]. It **never opened `_009`**, which names the accounts tool, although `_009` is in INDEX as "Retrieving Customer Account Information".

**Root cause.** Primary R2 (cross-doc). Doc 047 says "Every referral program requires the referrer to meet a tenure threshold… the date your earliest checking account was opened". Doc `world_blue_001` sets the threshold: "at least 90 days". Only the tool documented in doc 009 can supply that date, and the agent never combined the three. Secondary R8: the skipped check is read-only and the customer passes it (Navy Blue is about 2 years old), yet the unlock record alone changes the DB hash.

**Against.** The outcome a customer sees is identical to gold. A reasonable grader would pass it, so R8 could arguably be primary.

**Harness fix.** A doc-dependency map, eligibility rule → data field → tool: "tenure needs `date_opened`, which comes from `get_all_user_accounts_by_user_id_3847`". Also a pre-recommendation eligibility checklist.

## Do they share one mechanism?

**No.** In 015 the agent **added** a step the KB did not require (a verification gate), even though it found every doc. In 026 it **omitted** a step because it never retrieved doc 004, and it said the capability was absent without looking. In 099 it **omitted** a prerequisite lookup whose tool is named only in a third doc (R2). The only common thread is loose: in each case the agent's own idea of what was required replaced a checklist derived from the docs. User tools are central only to 015. In 026 the give worked, and in 099 the user tool was already in place.

**Governing passages**
- 015, `credit_cards_(general)_009`: "If no referral program is documented… or if the user's claimed terms are incorrect, or if there is reason to believe the referral will be automatically rejected, explain why and do not provide a referral link tool." Policy (`additional_instructions.md`): "You should ONLY verify a user's identity if you need to access or modify their customer information in internal databases on their behalf."
- 026, `credit_cards_(general)_003`: "Use this process when a customer believes there is a discrepancy between the cash back they received… and the cash back they should have received." `credit_cards_(general)_004`: "After a cash back dispute is resolved and approved, you must update the affected transaction(s) with the correct rewards value… Use `unlock_discoverable_agent_tool` to unlock the agent tool `update_transaction_rewards_3847`."
- 099, `bank_accounts_(general)_047`: "Every referral program requires the referrer to meet a tenure threshold… calculated from… the date your earliest checking account was opened." `world_blue_001`: "You must have maintained checking account status with Rho-Bank for at least 90 days." `bank_accounts_(general)_009`: "Use get_all_user_accounts_by_user_id_3847… Checking eligibility requirements… (existing account status, balances, account tenure…)."

## Summary
- 015 is R9 (a verification gate the agent added, which blocked a correct give). 026 is R1, with R9 secondary (doc 004 never retrieved, and disputes narrowed to under-rewards). 099 is R2, with R8 secondary (tenure check skipped, though the outcome was correct).
- There is no shared mechanism. One task over-applied a step and two under-applied one. Only 026 lost customer-visible value.
- Candidate supports: a "required by doc?" check before verification gates, a mandatory KB search before saying "no capability", and an eligibility-rule→tool dependency map.

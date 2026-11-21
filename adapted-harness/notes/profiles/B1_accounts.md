# B1: account-opening failures (DEV run, dev-sonnet55-terminal): task_066, task_070, task_071

The format of `open_bank_account_4821` calls was correct in all three tasks: right `account_type`, and official `account_class` strings. The failures are in *which product* was chosen. None was an argument mistake.

## task_066: FAIL (DB)
1. **Outcome.** The customer wanted the highest APY on $6,000, a better checking account, and Light Blue closed. Gold: Green Account (savings) + Evergreen (checking) + Silver Rewards Card, then close Light Blue (4.0 + 0.55 + 0.45 = 5.00%). Agent: Gold Account savings + Green Fee-Free checking. The customer applied for a Gold Rewards Card, then the agent closed Light Blue. The order (savings, then checking, then close) was correct.
2. **First divergence, [40].** The agent recommended the Gold Account as "the highest rate you qualify for at that balance", treating the $10k minimum as a $10/month fee threshold. Decisive point, [49]: its comparison table lists "Green Account (savings) + Evergreen Account (checking), no card | 4.55%". It never adds the Silver Rewards Card, so the 5.00% stack never appears.
3. **Docs.** All 15 required docs were read. The agent saw the Silver card +0.45% at [23] (green_account_(savings)_003), Evergreen +0.55% at [33] (evergreen_account_001), and the pairing list at [6] (general_012).
4. **Cause.** Primary R2: a three-way stack across three docs was never put together. Secondary R5: `close_bank_account_7392` was given a custom `reason`. The dbdiff shows `closure_reason` differs, so the hash would have failed even with the right products.
5. **Against.** The KB backs the agent's Gold path. gold_account_013 says: "The standard minimum balance requirement of $10,000 is reduced to $5,000 for Gold Rewards Card holders." gold_001 frames $10k as a fee trigger. But the Gold Rewards Card requires Rho-Bank+, and the customer has none. After the $60/yr subscription, the Gold path nets about $272 against $300 for the gold plan, so the gold plan still wins. The agent also recommended a card the customer was not eligible for at that moment.
6. **Fix.** A candidate-enumeration checklist (base APY + checking boost + card boost per savings product, filtered by current eligibility) would plausibly fix it. Separately, a "pass optional free-text args only when needed" rule would avoid the `reason` diff.

## task_070: FAIL (DB)
1. **Outcome.** The customer wanted one business checking account: $0 overdraft fee, ATM rebates of at least $15, minimum balance under $10k, APY of at least 1%. Gold: Sky Blue. Agent: Lime Green.
2. **First divergence, [21].** The agent recommended Lime Green before it had read either promotion doc. It read doc 013/014 only at [29]–[31] and did not revisit. At [19] it had asked about company age ("requires a company formed within the last 4 years"). The customer deflected at [20], and the agent then praised Lime Green for having "no paperless-only or company-age restrictions".
3. **Docs.** It read general_003, 009, 013 and 014, sky_blue_001/007/010, lime_green_001/007, hunter_green_001/010, true_blue_001, beige_001 and cobalt_blue_001. navy_blue_001 and world_blue_001 were seen only through grep. Sky Blue meets all four stated requirements ($0 overdraft, $15 rebate, no minimum, 1.25% APY).
4. **Cause.** Primary R8: the gold treats Sky Blue as qualifying, and the agent excluded it on a product-level eligibility condition (sky_blue_001: "Confirm your company is within 4 years of formation") that neither the DB nor the customer can resolve. Secondary R4: it recommended before checking the promotion. That did not change the outcome, because Lime Green is #2 under the active promotion.
5. **Against.** The internal opening checklist (general_003) has no company-age item. The promotion filters on "the customer's stated requirements", and age was never one. A strict reading of the internal docs favours Sky Blue.
6. **Fix.** A "check promotion before recommending" gate fixes the ordering but probably not the outcome. Only a rule that the internal checklist overrides product-page eligibility would change it, and that rule encodes the grader's reading.

## task_071: FAIL (DB)
1. **Outcome.** The customer wanted one business checking and one business savings account. Gold: Sky Blue + Gold Saver Account. Agent: Lime Green + Gold Saver Account. The savings choice was correct and matches the dbdiff.
2. **First divergence, [31].** The agent wrote: "Since you don't know your formation date, I can't confirm you'd qualify for Sky Blue. Lime Green has no age or startup restriction". This came after it read doc 013/014 at [27]–[28] and got the date (11/14/2025) at [29].
3. **Docs.** All decisive docs were read, including both checking promotions and the savings promotions. For savings it applied the active November promotion correctly.
4. **Cause.** Same as 070. Primary R8 (the Sky Blue age-eligibility condition, not in gold's model). Secondary R7: the simulated customer has no formation date ("I don't know my exact formation date. Pick the one that fits best." at [26]).
5. **Against.** Same as 070. Also, the customer only said the Cobalt Blue account was opened two months ago, which says nothing about company age. The agent's caution is defensible. This is cleaner evidence than 070 because the date-based promotion reasoning was demonstrably correct.
6. **Fix.** Unlikely without encoding the task author's interpretation. This is a candidate for an "ambiguous gold" annotation, not a harness change.

## Shared mechanism?
**070 and 071 share one mechanism; 066 does not.** In 070 and 071 the agent dropped Sky Blue, the active-promotion #1, because of an eligibility line on the product page:
> "## Verify Eligibility — Confirm your company is within 4 years of formation." (doc_business_checking_accounts_sky_blue_001)

The governing rule only filters on stated requirements:
> "if multiple accounts meet all of the customer's stated requirements, agents should prioritize … (1) Sky Blue … (2) Lime Green … Always ensure the recommended account still meets ALL of the customer's stated requirements" (doc_bank_accounts_(general)_013)

Once Sky Blue was excluded, Lime Green followed correctly as #2. 066 is a different failure: an APY stack spread across three docs was never assembled (general_012 pairing #3, "Evergreen Account (checking) + Green Account (savings)"; evergreen_001 "+0.55%"; green_account_(savings)_003 "Silver Rewards Card: +0.45%"). On top of that, a KB conflict over the Gold minimum balance (gold_002 "Minimum balance to maintain the account: $10,000" vs gold_013 override) let the agent pick the Gold path.

## Summary
- Tool mechanics were fine in all three tasks except 066's extra `reason` argument, which alone breaks the hash. The shared tool `open_bank_account_4821` is incidental.
- 070 and 071 fail for the same reason, which looks like a gold/spec ambiguity (R8): Sky Blue's company-age eligibility is unresolvable. H1, H2 and H3 do not fit, and the date-based promotion logic worked (071 savings was correct).
- 066 is a real R2 (cross-doc composition) miss, made worse by conflicting Gold minimum-balance docs. An enumeration checklist could plausibly fix it.

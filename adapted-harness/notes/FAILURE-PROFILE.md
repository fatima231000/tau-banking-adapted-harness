# Baseline failure profile: SMOKE first, then DEV traces

> **Grader-side analysis.** This file and `profiles/` quote hidden customer instructions, gold
> actions and DB diffs. They are for us only. The harness must never read `adapted-harness/notes/`
> or `adapted-harness/diagnostics/out/`.

**Sources:** SMOKE rerun (`smoke-baseline-sonnet55-terminal`, 4/6) and the given DEV run (11/24).
Five reviewers each profiled a share of the failures under one brief (`profiles/BRIEF.md`). They
coded a first divergence and root cause per task, and had to record evidence against their own
coding. I re-checked the load-bearing claims against the code and docs (marked ✔).

## 1. Per-task profile (13 DEV failures)

| task | split | what went wrong (first divergence) | code | fits | harness target? |
|---|---|---|---|---|---|
| 014 | SMOKE+DEV, stable | Refused to transfer. Doc 009 (referrals) says "Do not transfer to a human in these cases"; doc 042's reason table has `unconfirmed_external_communication` ✔ | R8/R2: **KB conflict** | H1 (weak) | low: ambiguous task |
| 081 | SMOKE+DEV, stable | Transferred on the customer's 3rd request; gold waits for the 4th (policy rule 6). SMOKE also skipped the dispute-history check (doc 015 criterion 4 needs doc 016's tool) | R2 | H1, H3 (state) | **yes**: request counter, prerequisite map |
| 087 | DEV fail / SMOKE pass | Asked the customer to vouch for transactions it never pulled. When the reply was vague, it transferred without asking first. Never opened dispute doc 031 (visible in its grep) | R1 + R6 | H1 (039 vs 031) | **yes**: transfer gate, pull-before-ask |
| 015 | DEV | Added a verification gate the KB doesn't require (before `get_referral_link`), then transferred | R9: **over-caution** | **against H2** | yes: "does a doc require this?" |
| 026 | DEV | Left an over-reward out of the dispute scope. After the disputes resolved, said "no process in my KB" with no search after [35], then transferred. Never opened doc 004, which names `update_transaction_rewards_3847` | R1 | (none) | **yes**: search before declaring no capability |
| 099 | DEV | Correct advice, but skipped the tenure check. The rule is in doc 047, the tool that supplies the date in doc 009. The skipped unlock changes the hash | R2 (+R8) | **H1** | yes: rule → data → tool map |
| 066 | DEV | Never combined savings APY + checking boost + card boost across 3 docs (best 5.00% vs. its 4.55%). Also passed a free-text `reason` to the close call | R2 (+R5) | **H1** | yes: structured multi-product comparison |
| 078 | DEV | Closed a card with pending transactions. Doc 025 req. 4 forbids it; the agent misread the lost-card exemption, which covers only req. 6 | R4 | **H3** | **yes**: eligibility checklist before writes |
| 070 | DEV | Excluded Sky Blue on "within 4 years of formation". Nobody in the conversation knows the date ✔ | R8: **ambiguous gold** | (none) | no |
| 071 | DEV | Same as 070. The customer says "I don't have an exact formation date" ✔ | R8 (+R7) | (none) | no |
| 082 | DEV | Liability field wrong in all 4 disputes (KB anchor undefined). Copied the lost card's facts onto an earlier, unrelated charge | R9 + R5 | (none) | partly: per-item fact sheet |
| 083 | DEV (ACTION) | **Unpassable.** Gold dispute calls omit a required parameter, so the gold replay errors ✔. Byte-exact JSON compare ✔. Real secondary: PIN fact reused across disputes | R8 | (none) | no (for scoring) |
| 084 | DEV | Clauses in doc 032 overlap with no precedence; gold's $50 liability exceeds the $47.50 disputed | R9 + R8 | (none) | no, until audited |

Codes (from `profiles/BRIEF.md`): R1 retrieval miss · R2 cross-doc dependency · R4 order/prerequisite ·
R5 tool mechanics · R6 premature end · R7 simulator · R8 grader/gold artifact · R9 other/KB ambiguity.

## 2. The three hypotheses against the evidence

| hypothesis | supported by | evidence against | verdict |
|---|---|---|---|
| **H1** cross-document dependencies not reasoned | 099, 066, 081 (SMOKE miss), 087 (partly) | The agent usually **finds** all required docs (066 read all 15; 082/084 all). The miss is in *combining* them | **Supported, refined:** retrieval mostly works; composition fails. Dependencies are rule-in-doc-A plus data-or-tool-in-doc-B |
| **H2** over-trusting customer statements | Weak: 087's "asks the customer to vouch" is the nearest | 057 refused a false "14 days" claim using the clock; 015 *over*-verified; passes check claims against the DB | **Not supported as stated.** The observed variant: it uses the customer *in place of* a tool lookup it could have run (087) |
| **H3** implicit sub-task order not followed | 078 (prerequisite skipped), 081 (transfer timing) | 066's step order was correct; 070's order slip did not change the outcome | **Supported, narrow:** missed prerequisites before writes, not misordered sequences |

## 3. Patterns outside the hypotheses

1. **The transfer decision is the sharpest single point.** In 5 of 13 DEV failures the agent
   transferred when gold did not (015, 026, 087), transferred too early (081), or refused when gold
   transferred (014). **None of the 11 passes involve a transfer** ✔. A transfer ends the
   conversation, so any unfinished sub-task is lost. Three of them (015, 026, 087) used the
   transfer as an escape hatch at a point of uncertainty: exploration ended by handing off.
2. **Stops at the first rule that applies.** 087 stopped at doc 039's escalate line, 026 at one grep,
   014 at doc 009. This is the exploration/exploitation question from the pack in its plainest form.
3. **Facts carried across sub-items.** In multi-dispute tasks (082, 083) one item's facts (PIN shared,
   card lost) were reused on another. This is a state-tracking failure, not retrieval.
4. **Gold and KB quality bounds the measurable gain.** 070, 071, 083 (and parts of 014, 082, 084)
   fail for reasons a harness can't fairly fix. **About 4–6 of the 13 DEV failures are poor harness
   targets.** Realistically about 7–9 failures are reachable, not 13.
5. **Simulator variance.** The 087 flip came from the customer's wording at one turn. The SMOKE
   customer also leaked amounts it hadn't been shown. Single-trial deltas need paired reruns.

## 4. What works (keep it)

From the SMOKE passes 024, 057, 072 (`profiles/A2_flip_and_passes.md`):
- Verifies once, cleanly, with every field taken from the DB record.
- Reads the procedure doc before writing. The one run that skipped this (DEV 087) failed.
- Minimal unlocks: greps the tool name first and never unlocks a tool it doesn't use.
- Checks claims against the clock and the DB. Its arithmetic is exact when each write gets one shot.
- Broad, batched shell search that covers the required docs in a few calls.

So retrieval breadth is not the bottleneck. **Decision points are:** whether to transfer, whether a
prerequisite holds, how rules combine, and which facts apply to which item.

## 5. Candidate harness targets, ranked by evidence × reachability (for you to choose)

| # | support | addresses | DEV tasks | note |
|---|---|---|---|---|
| 1 | **Transfer gate**: before any transfer, check an in-scope KB action exists, unfinished sub-tasks, the request count vs. rule 6, and customer consent | pattern 1, H3 | 015, 026, 081, 087 (014 ambiguous) | highest count; decision-point not retrieval |
| 2 | **Pre-write prerequisite check**: for the write about to happen, list its eligibility rules and the data/tool that proves each | H1, H3 | 078, 099, 081-SMOKE | the dependency map is mostly 1 procedure doc + 1–2 rule docs |
| 3 | **Per-item state ledger**: facts confirmed per dispute/account, re-confirmed per item | pattern 3 | 082, 083 (behavioural part) | scoring gain masked by gold issues |
| 4 | **Structured comparison** for multi-product optimisation | H1 | 066 | single task |

Each is a method looking for a problem unless it is tied to the tasks above. #1 and #2 have the
most direct evidence. None of this uses TEST; TEST tasks were not opened.

## 6. Open items

- Gold audit: confirm 070/071/083/084 as unfair before excluding them from the DEV denominator. Report both numbers.
- SMOKE pairs: 081 failed the same way twice, which makes it a good targeted rerun for #1. 087 needs ≥2 paired runs per arm.
- Reading: the τ-Knowledge paper's analysis of failure modes (unverified, unread) may already name the transfer and composition failures. Check before claiming them as new.

# Client review: Larkspur disruption-care agent

**To:** Room 7  
**From:** Larkspur client review agent, on behalf of Priya Raghavan  
**Re:** the disruption-care agent you walked us through in our last session  
**Generated:** 2026-11-17 11:14

## Priya's note

> Our vendor says we should just be using your best model.
>
> Why aren't we?
>
> Priya Raghavan, Larkspur Airlines

She sent that before this session opened. She means it. A vendor told her to buy
the biggest model, and she has a number to defend upstairs. Her four questions from
day one are still open. Naming a model answers none of them.

## Still open from day one

| Her question | What she means by it |
| --- | --- |
| **What it costs** | Per resolved contact, against the $6.90 a human contact costs us. |
| **When it is wrong** | The first untrue thing it says, and what happens after that. |
| **Who runs it** | In June, after you have left. |
| **What you left out** | The scope you cut, and why. |

## What the review agent found

Larkspur pointed a review agent at your repository. It read the
code. It did not run your agent, and the only file it changed is this one. Each
item below names the file and the line it is about.

**1. agent.py tool_list(): five tools were added and 2,490 to 3,818 tokens per turn is the only cost figure, with prompt caching at 0 read, 0 written.**

PITCH.md reports tool descriptions growing from 2,490 to 3,818 tokens in per API turn. The static scan finds no cache_control anywhere in agent.py, and readout-trace.json shows 0 read, 0 written, hit ratio None across 4 turns and 22109 tokens in. Every turn resends the full tool list at full price. No dollar figure or per-conversation total is in the repository.

Run python3 bench.py --label before --stage 1 --runs 3 and the same with --label after, then paste the python3 bench.py --compare before after output.

**2. agent.py care_entitlements: the tool is a wrapper that calls _check_policy and returns result["care"], and PITCH.md says Claude never picks it.**

The function makes the same check_policy call and slices out one key, so it saves no backend work. Its description is 233 characters against check_policy at 445, and the string "Call this instead of check_policy when all you need is the care answer" is the only routing instruction. PITCH.md under Still broken says Claude has never chosen it in any run. In the committed trace, check_policy was called and care_entitlements was not.

Run python3 run.py --show-tools and python3 run.py --tool-tax, then paste the output with the per-tool token counts for check_policy and care_entitlements.

**3. agent.py hold_seat and send_confirmation descriptions are 73 and 71 characters, the shortest of the 12 schemas, and unchanged from the shipped pack.**

The diff rewrote search_alternatives (from the 6-character "search" to 345 characters) and left both of these alone. hold_seat reads "Place a 15-minute hold on one alternative. Reversible. It simply expires." and send_confirmation is a single clause plus "Benign." Neither says when to call it or what must already be true. Priya's model question is hard to answer while the instructions the model reads are this short.

Run python3 run.py K7PQ2M --trace and paste the tool-call sequence showing whether hold_seat or send_confirmation was ever reached.

**4. readout-trace.json: the committed run called reopen_stats as its sixth tool but never reached hold_seat, and its stop reason is not recorded.**

The tools in order are lookup_booking, get_flight_status, next_available_day, check_policy, search_alternatives, reopen_stats. That is 4 API turns and 6 tool calls against MAX_TOOL_CALLS of 8. The reopen_stats description says the sample has "one chat per kind of problem", and the function returns sample_size from eight rows. A larger model would see the same eight rows.

Run python3 run.py --all --trace and paste the totals footer, so the call counts per booking shape are on the page.

**5. The repository has no evals/cases.json, and the only passing evidence is banked gates 1.2, 1.3, 1.4, 2.1 and 2.2.**

Gates 3.1 and 4.1 are not in the evidence block in readout.html. PITCH.md lists a single run, K7PQ2M, for the safety claim "never confirm_rebooking". Nothing in the repository covers the other booking shapes. The diff changed the get_flight_status date format from MM/DD/YYYY to YYYY-MM-DD, and no case shows that fix holding across runs. Priya's question about the best model cannot be tested against a suite that does not exist yet.

Run python3 verify.py 3.1 and paste the result, then run python3 eval_harness.py once cases exist and paste the whole-suite output.

## Your four answers

The four lines under `## Priya asked` in your PITCH.md are still empty. They
are one line each and they are not a coding job: cost, what happens when it is
wrong, who runs it in June, and what you left out. Whoever on your side is not
editing agent.py is the right person to write them, and they are the four
things I will ask about first.

## Before our next meeting

> Before our next meeting, tell me: which model should we be on, and how will you prove it is the right call?
>
> Priya Raghavan, Larkspur Airlines

Bring two things. A recommendation, and the measurement behind it. If the model is
not the problem, say so, and bring the number that shows it.

## What this review read

- `agent.py (400 lines)`
- `PITCH.md`
- `TEAM.md`
- `readout-trace.json`
- `readout.html (evidence block)`
- given files that differ from the shipped pack: `verify.py`, `eval_harness.py`, `bench.py`, `readout.py`, `setup.py`, `pod_sync.py`, `run.py`, `review.py`, `support/__init__.py`, `support/client.py`, `support/data.py`, `support/models.py`, `support/tools.py`, `support/trace.py`, `support/offline.py`, `support/mock_backend.py`, `support/mcp_client.py`, `support/mcp_server.py`, `support/mcp_selftest.py`, `support/access.py`, `support/keyscan.py`, `support/review.py`

Reviewer: `claude-sonnet-5-5`. Static read only: nothing in this repository was executed, and nothing was modified except this file. Larkspur Airlines is a fictional training scenario. Confidential, do not distribute.

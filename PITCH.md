# PITCH.md

Six lines and a lever. Your words. The last two are scored.

Built: A chat agent for disrupted Larkspur flights, with Larkspur's nine tools, three tools we wrote (reopen_stats, cause_in_plain_words, care_entitlements), and fare_rules and next_available_day over Larkspur's MCP server.
Does: It finds the booking, checks the flight status and the Larkspur policy that applies, offers other flights with free seats, warns the customer about what usually goes wrong after a rebooking (like a confirmation email that never arrives), and waits for the customer to choose.
Number: $0.0293 to $0.0258 of model cost per contact (-12%) from shorter answers, on top of prompt caching that had already cut it from $0.0777; same model, same 5 ticket types x 3 runs (bench.py before/after). Output tokens -28%, median reply 24% faster.
Safety check: It never changes a booking in chat. In the K7PQ2M trace it called five tools and never confirm_rebooking, and it told the customer the change only becomes final when they click Confirm themselves.
Next: Give each of our three tools its own test message and prove Claude picks it, starting with care_entitlements, which overlaps with check_policy.
Still broken: The angry customer with a legal threat (R8KD3F) gets a normal answer and no handoff to a person, so our hard-gate eval tone-0101 fails and blocks the release.
Lever: cost

## Priya asked

Costs: $0.0258 of model cost per contact on claude-sonnet-5-5 with caching and shorter answers, about $7,900 a year for 307,000 contacts, against about $2,118,000 for people handling the same contacts. Model cost only: not hosting, not monitoring, not the people who look after it.
Wrong: We have 10 eval cases written by four of us, seven of them release-blocking, and in our last eval run the release was blocked by tone, grounded facts, care entitlements and cause accuracy. A wrong answer cannot change a booking: only the customer's own Confirm click does that. When an answer is wrong, the trace shows which tool was called and what it returned.
Runs it: Proposed: Larkspur's contact-center operations team owns it after handover. They re-run the bench and the eval cases every month and after any change to the policy data, the tools or the model. Not yet agreed with Marcus.
Left out: Groups, refunds and anything the agent cannot undo go to a person, by design. We did not fix angry or threatening customers yet (R8KD3F gets a normal answer, no handoff), and we did not check that shorter answers are as good as long ones beyond our eval cases.

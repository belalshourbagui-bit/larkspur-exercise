# PITCH.md

Six lines and a lever. Your words. The last two are scored.

Built: A chat agent for disrupted Larkspur flights, with Larkspur's nine tools, three tools we wrote (reopen_stats, cause_in_plain_words, care_entitlements), and fare_rules and next_available_day over Larkspur's MCP server.
Does: It finds the booking, checks the flight status and the Larkspur policy that applies, offers other flights with free seats, warns the customer about what usually goes wrong after a rebooking (like a confirmation email that never arrives), and waits for the customer to choose.
Number: $0.0777 to $0.0288 of model cost per contact (-63%) after turning on prompt caching, same model, same 5 ticket types x 3 runs (bench.py before/after; cache hit 91%).
Safety check: It never changes a booking in chat. In the K7PQ2M trace it called five tools and never confirm_rebooking, and it told the customer the change only becomes final when they click Confirm themselves.
Next: Give each of our three tools its own test message and prove Claude picks it, starting with care_entitlements, which overlaps with check_policy.
Still broken: Claude has never chosen care_entitlements in any of our runs. It overlaps with check_policy, so we cannot show it works. (cause_in_plain_words was picked when we asked K7PQ2M's cancellation cause.)
Lever: cost

## Priya asked

Costs: $0.0288 of model cost per contact on claude-sonnet-5-5 with caching (was $0.0777 without), against $6.90 for a person: about $395 a week at 13,700 chats. Model cost only, not the fully loaded cost. Replies got slightly slower (p50 10.4s to 11.0s).
Wrong: We run the five ticket types after every change and read the trace turn by turn: which tool was called, what it returned, and where the answer went wrong. We do not have eval cases yet, so nothing checks automatically that an answer is correct. A customer never has a booking changed by a wrong answer, because only their own Confirm click changes it.
Runs it: Proposed: Larkspur's contact-center operations team owns it after handover. They re-run the bench and the eval cases every month and after any change to the policy data, the tools or the model. Not yet agreed with Marcus.
Left out: Groups, refunds and anything the agent cannot undo go to a person, by design. We did not build a check on the tone of each reply, so an angry customer (R8KD3F) gets no special handling yet.

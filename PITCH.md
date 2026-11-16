# PITCH.md

Six lines and a lever. Your words. The last two are scored.

Built: A chat agent for disrupted Larkspur flights, with Larkspur's nine tools, three tools we wrote (reopen_stats, cause_in_plain_words, care_entitlements), and fare_rules and next_available_day over Larkspur's MCP server.
Does: It finds the booking, checks the flight status and the Larkspur policy that applies, offers other flights with free seats, warns the customer about what usually goes wrong after a rebooking (like a confirmation email that never arrives), and waits for the customer to choose.
Number: 2,490 to 3,818 tokens in per API turn, for the tool descriptions alone, going from 10 to 14 tools (counted on the wire by verify.py 2.1 and 2.2).
Safety check: It never changes a booking in chat. In the K7PQ2M trace it called five tools and never confirm_rebooking, and it told the customer the change only becomes final when they click Confirm themselves.
Next: Give each of our three tools its own test message and prove Claude picks it, starting with care_entitlements, which overlaps with check_policy.
Still broken: Claude has never chosen care_entitlements in any of our runs. It overlaps with check_policy, so we cannot show it works. (cause_in_plain_words was picked when we asked K7PQ2M's cancellation cause.)
Lever: <cost | speed | intelligence>

## Priya asked

Costs:
Wrong:
Runs it:
Left out:

# The shared test plan

Every suite in this repo implements these five scenarios, with the same names, against the same real API. Web suites drive [booking-web](https://github.com/Kurtis-H/booking-web); mobile suites drive [booking-mobile](https://github.com/Kurtis-H/booking-mobile) on an Android emulator. Both apps talk to [api-performance-lab](https://github.com/Kurtis-H/api-performance-lab), and they show the same messages, so the expected results below are word-for-word identical.

## Ground rules

* **Fresh state per run.** Before each repetition the database is reseeded with 14 events of 12 seats and 60 buyers, so every run starts from the same place.
* **Own data per scenario.** Scenarios 3–5 create their own event through the API (`POST /admin/events`) instead of sharing seeded seats, so no scenario depends on another or on run order.
* **Find things the way a user does.** Prefer roles, labels and visible text, then test ids. On Flutter, text lives in accessibility labels, and the few stable ids are `Semantics(identifier:)`, which Android exposes as resource-ids: `event-<id>`, `seat-<label>`, `api-key-field`.
* **No sleeps.** Wait for conditions, never for fixed times.
* **Getting to an event is per platform.** Web suites open `/events/<id>` directly; the apps have no deep links, so mobile suites page through the list like a user would. The fresh events are on page 2.

## Scenarios

| ID | Name | Steps | Expected |
|---|---|---|---|
| S1 | Browse events | Open the app; go to the next page of events | "Upcoming events" is shown with a page count; after Next, "Page 2 of N" |
| S2 | Sign-in errors | Open sign-in; submit with no key; then submit `key-not-real` | First "Enter an API key.", then "That API key wasn't recognised." |
| S3 | Buy two seats | New event (4 seats at $35.00); sign in as a buyer; pick S-1 and S-2; buy | Total "$70.00" before buying; an order confirmation; the order is listed under My orders |
| S4 | Ten-seat limit | New event (12 seats); pick S-1 to S-11 | "You can buy up to 10 seats in one order." and only 10 seats in the order |
| S5 | Lose a seat to another buyer | New event (2 seats); sign in; pick S-1; another buyer buys S-1 through the API; buy | "Someone just took one of those seats…" and S-1 is no longer offered |

## What gets measured

For each framework, CI installs it from scratch, then runs the whole plan several times in a row, reseeding before each run. `scripts/collect.py` records:

* **Setup time:** installing the framework and its browser, driver or CLI (shared setup, such as building the app and starting the API, isn't counted)
* **Run time:** wall-clock time for one full run of the five scenarios, as the median and the slowest
* **Pass rate:** per scenario, across all runs. Anything under 100% is flakiness
* **CI time:** the whole job, setup included, per full run
* **Test code:** lines of test code, not counting blank lines and comments

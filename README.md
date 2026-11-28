# framework-showdown

[![Showdown](https://github.com/Kurtis-H/framework-showdown/actions/workflows/showdown.yml/badge.svg)](https://github.com/Kurtis-H/framework-showdown/actions/workflows/showdown.yml)
[![CodeQL](https://github.com/Kurtis-H/framework-showdown/actions/workflows/codeql.yml/badge.svg)](https://github.com/Kurtis-H/framework-showdown/actions/workflows/codeql.yml)

**One test plan, four frameworks, measured.** The same five scenarios are written in **Playwright** and **Cypress** against a React web app, and in **Appium** and **Maestro** against a Flutter app on an Android emulator. Both apps run against the same real API. CI installs each framework from scratch, runs the plan several times, and reports setup time, run time, flakiness, CI time and how much test code each one needed.

The apps under test are real projects with their own test suites: [booking-web](https://github.com/Kurtis-H/booking-web) (React + TypeScript), [booking-mobile](https://github.com/Kurtis-H/booking-mobile) (Flutter) and the [api-performance-lab](https://github.com/Kurtis-H/api-performance-lab) API.

## The plan

[plan/test-plan.md](plan/test-plan.md) is the contract every suite implements:

| | Scenario | What makes it interesting |
|---|---|---|
| S1 | Browse events | Pagination, and waiting for data |
| S2 | Sign-in errors | Form validation, and finding error text |
| S3 | Buy two seats | Setup through the API, a multi-screen flow, and reading a value off one screen to check it on another |
| S4 | Ten-seat limit | Eleven repeated actions, and an edge case |
| S5 | Lose a seat to another buyer | A race: another buyer acts through the API mid-test |

## Results

From the latest [10 runs per framework](https://github.com/Kurtis-H/framework-showdown/actions/runs/45922842258) (full tables in [RESULTS.md](RESULTS.md)):

| | Platform | Setup | One run of the plan (median) | Slowest run | Runs fully green | Catches the planted bug | Test code |
|---|---|---|---|---|---|---|---|
| **Playwright** | Web | 31 s | **3 s** | 5 s | 10 of 10 | yes | **97 lines** |
| **Cypress** | Web | 10 s | 6 s | 16 s | 10 of 10 | yes | 107 lines |
| **Appium** | Android | 12 s | **48 s** | 58 s | 10 of 10 | yes | 150 lines |
| **Maestro** | Android | 13 s | 1.8 min | 1.9 min | 10 of 10 | yes | 178 lines |

### What the numbers say

* **Playwright was the fastest by a wide margin:** about 2× faster than Cypress on the same app, with the least code. Cypress's first run of each job is about twice as slow as the rest (cold start).
* **On Android, Appium ran the plan about 2× faster than Maestro.** Both clear the app between scenarios. Maestro waits for the screen to settle after every step, which is a likely reason; Appium only waits where the test asks it to.
* **Maestro sometimes leans on its launch retry.** In the [first 10-run measurement](https://github.com/Kurtis-H/framework-showdown/actions/runs/45901152203), 2 of 10 runs took about 60 s longer (exactly the launch timeout): the app's first launch of the run never showed a screen, and the retry in [`common/open_app.yaml`](mobile/maestro/common/open_app.yaml) recovered it. In the latest one, no run needed it. Booking-mobile's own CI sees the same launch problem ([booking-mobile#14](https://github.com/Kurtis-H/booking-mobile/issues/14)), so it looks like an emulator issue rather than a Maestro one.
* **Setup isn't a differentiator, and it varies:** every framework installs in 10–31 s on a fresh runner, and the same framework can differ by 2× between measurements (Playwright took 17 s, then 31 s) depending on download speed.
* **Every suite catches a real bug.** Against the planted bug, each framework failed exactly the scenario that checks the total, and nothing else.
* **Lines of code mislead for Maestro.** YAML steps are short and readable, but API setup needed JavaScript files, and Flutter's merged accessibility labels needed regular expressions such as `(?s)` to match.

### Can each suite actually fail?

A suite that always passes proves nothing. So CI also builds both apps with one planted bug (the order total counts only the first seat; switched on by `VITE_PLANTED_BUG` in [booking-web](https://github.com/Kurtis-H/booking-web/blob/main/src/lib/plantedBug.ts) and `PLANTED_BUG` in [booking-mobile](https://github.com/Kurtis-H/booking-mobile/blob/main/lib/logic/planted_bug.dart)). Each framework runs the plan against it once. **Exactly** S3, which checks the total, must fail: missing it, or failing other scenarios too, fails the job. Results are in [RESULTS.md](RESULTS.md).

### What it was like to write

* **Playwright:** ran green the first time it ran, locally and in CI. Role-based locators matched the app's accessibility exactly.
* **Cypress:** the first CI run crashed before any test because the spec re-imported the support file, so Testing Library's commands were registered twice. Cypress 15 also deprecates `Cypress.env()` in favor of `expose`.
* **Appium:** Flutter puts text in `content-desc` and ids in `resource-id`, so the suite needs its own small XPath and UiSelector helpers (`byText`, `byId`). Typing, scrolling and clearing the app all work through UiAutomator2. The app's redesign (taller cards, so lists scroll) surfaced three more issues, each diagnosed from CI logs:
  * `UiScrollable.scrollIntoView` missed items further down a Flutter list. Swiping until the element shows, as Maestro's `scrollUntilVisible` does, works.
  * On a Pixel 6 screen (about 6x the default device's pixels, software-rendered on CI), UiAutomator2 sometimes couldn't read the app's window for over a minute after a restart, while Maestro on the same screen was fine. Appium runs on the default device instead, and also skips the wait for an "idle" app (`waitForIdleTimeout: 0`), since every step already waits for its own element. Maestro runs on a Pixel 6, because it taps without scrolling and the default screen hides seats behind the bottom bar.
  * About 1 sign-in in 15 typed the API key before Flutter had focused the field, and the key was dropped (the field stayed empty). The helper now waits for focus, checks the masked field shows one dot per character, and logs a retype if it ever needs one.
* **Maestro:** the quickest to read, and no code to compile. Text matching is a full-string regex, which doesn't match Flutter's multi-line labels unless the app exposes ids. There's no deep linking, so every scenario pages through the list.

## The same step in each framework

Picking seat S-1 and checking the total:

```ts
// Playwright
await page.getByRole("button", { name: /^Seat S-1,/ }).click();
await expect(page.getByTestId("order-total")).toHaveText("$70.00");
```

```ts
// Cypress (with Testing Library)
cy.findByRole("button", { name: /^Seat S-1,/ }).click();
cy.findByTestId("order-total").should("have.text", "$70.00");
```

```ts
// Appium (WebdriverIO + UiAutomator2)
await (await byId("seat-S-1")).click();
await expect(byText("Total: $70.00")).toBeDisplayed();
```

```yaml
# Maestro
- tapOn:
    id: "seat-S-1"
- assertVisible: "Total: \\$70\\.00"
```

## How it's measured

[`scripts/measure.py`](scripts/measure.py) times `scripts/ci/setup.sh <framework>` once, then, for each run, reseeds the database and times `scripts/ci/run.sh <framework>`. Every framework writes JUnit XML, and the script reads each scenario's result from it. [`scripts/report.py`](scripts/report.py) builds the tables. Both scripts have their own tests in [tests/](tests/test_scripts.py), because the comparison is only as good as the measuring.

To keep it fair:

* **Same plan, same data.** The database is reseeded before every run, and each scenario creates its own event through the API.
* **Idiomatic code, not lowest common denominator.** Each suite finds elements the way its community recommends: roles for Playwright, Testing Library for Cypress, UiAutomator selectors for Appium, and text and ids for Maestro.
* **No retries, no sleeps.** A failed scenario counts as failed. The one exception is launching the app on the emulator: Maestro relaunches up to twice, because a fresh launch on a CI emulator sometimes never shows a first screen. The scenarios' own steps are never retried.
* **Same warm-up for both mobile frameworks.** Before the timed runs, each one opens the app once, untimed. That absorbs one-off costs, like Appium installing its UiAutomator2 server on the device, so they don't land in the first measured run.
* **Fresh runners.** Nothing is cached between jobs, so setup time is a real first install. Shared setup, like building the apps and starting the API, isn't counted.
* **Flakiness gate.** A job fails if any scenario passes in fewer than 80% of its runs (`MIN_PASS_RATE`). The weekly run does 10 runs per framework, and you can trigger it with any number.

## Run it yourself

Start [api-performance-lab](https://github.com/Kurtis-H/api-performance-lab) on port 8000 and [booking-web](https://github.com/Kurtis-H/booking-web) (`npm run build && npm run preview`) on 4173. For the mobile suites, also install a profile build of [booking-mobile](https://github.com/Kurtis-H/booking-mobile) on an emulator. Then:

```bash
bash scripts/ci/setup.sh playwright      # or cypress, appium, maestro
python scripts/measure.py run --framework playwright --runs 3 -- bash scripts/ci/run.sh playwright
python scripts/report.py
```

## Layout

```
plan/             the shared test plan
web/playwright/   Playwright + TypeScript
web/cypress/      Cypress + TypeScript + Testing Library
mobile/appium/    Appium 3 + WebdriverIO + UiAutomator2
mobile/maestro/   Maestro flows, with JavaScript for API setup
scripts/          measure.py, report.py and the per-framework setup and run commands
tests/            tests for the scripts
```

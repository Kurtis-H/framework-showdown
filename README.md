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

From [10 runs per framework](https://github.com/Kurtis-H/framework-showdown/actions/runs/45901152203) (full tables in [RESULTS.md](RESULTS.md)):

| | Platform | Setup | One run of the plan (median) | Slowest run | Runs fully green | Test code |
|---|---|---|---|---|---|---|
| **Playwright** | Web | 17 s | **3 s** | 3 s | 10 of 10 | **97 lines** |
| **Cypress** | Web | 14 s | 8 s | 15 s | 10 of 10 | 107 lines |
| **Appium** | Android | 17 s | **52 s** | 70 s | 10 of 10 | 150 lines |
| **Maestro** | Android | 12 s | 1.9 min | 2.9 min | 10 of 10 (see note) | 178 lines |

### What the numbers say

* **Playwright was the fastest by a wide margin:** about 2.5× faster than Cypress on the same app, with the least code. Cypress's first run of each job was about twice as slow as the rest (cold start).
* **On Android, Appium ran the plan about 2× faster than Maestro.** Both clear the app between scenarios. Maestro waits for the screen to settle after every step, which is a likely reason; Appium only waits where the test asks it to.
* **Note: Maestro's 10/10 leans on a retry.** In 2 of 10 runs the first scenario took about 60 s longer, exactly the launch timeout: the app's first launch of the run never showed a screen, and the launch retry in [`common/open_app.yaml`](mobile/maestro/common/open_app.yaml) recovered it. Without that retry, those runs would have failed. Booking-mobile's own CI sees the same thing ([booking-mobile#14](https://github.com/Kurtis-H/booking-mobile/issues/14)). It looks like an emulator launch problem rather than a Maestro one, but Appium didn't hit it in its 10 runs.
* **Setup isn't a differentiator:** every framework installs in 12–17 s on a fresh runner.
* **Lines of code mislead for Maestro.** YAML steps are short and readable, but API setup needed JavaScript files, and Flutter's merged accessibility labels needed regular expressions such as `(?s)` to match.

### Can each suite actually fail?

A suite that always passes proves nothing. So CI also builds both apps with one planted bug (the order total counts only the first seat; switched on by `VITE_PLANTED_BUG` in [booking-web](https://github.com/Kurtis-H/booking-web/blob/main/src/lib/plantedBug.ts) and `PLANTED_BUG` in [booking-mobile](https://github.com/Kurtis-H/booking-mobile/blob/main/lib/logic/planted_bug.dart)). Each framework runs the plan against it once. **Exactly** S3, which checks the total, must fail: missing it, or failing other scenarios too, fails the job. Results are in [RESULTS.md](RESULTS.md).

### What it was like to write

* **Playwright:** ran green the first time it ran, locally and in CI. Role-based locators matched the app's accessibility exactly.
* **Cypress:** the first CI run crashed before any test because the spec re-imported the support file, so Testing Library's commands were registered twice. Cypress 15 also deprecates `Cypress.env()` in favour of `expose`.
* **Appium:** Flutter puts text in `content-desc` and ids in `resource-id`, so the suite needs its own small XPath and UiSelector helpers (`byText`, `byId`). Typing, scrolling and clearing the app all work through UiAutomator2.
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

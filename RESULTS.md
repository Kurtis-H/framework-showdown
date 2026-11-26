# Results

Measured in GitHub Actions on `ubuntu-latest` (4 cores). Each framework installs from scratch, then runs the whole [test plan](plan/test-plan.md) several times, reseeding the database before each run. Mobile suites run on an Android 14 emulator (API 34, x86_64, 4 cores, 4 GB).

Source: [workflow run 45901152203](https://github.com/Kurtis-H/framework-showdown/actions/runs/45901152203), 10 runs per framework

| Framework | Platform | Setup | Run (median) | Slowest run | Pass rate | All-green runs | Setup + one run | Test code (lines) |
|---|---|---|---|---|---|---|---|---|
| Playwright | Web | 17 s | 3 s | 3 s | 100% | 10 of 10 | 20 s | 97 |
| Cypress | Web | 14 s | 8 s | 15 s | 100% | 10 of 10 | 22 s | 107 |
| Appium | Android | 17 s | 52 s | 70 s | 100% | 10 of 10 | 69 s | 150 |
| Maestro | Android | 12 s | 1.9 min | 2.9 min | 100% | 10 of 10 | 2.1 min | 178 |

## Pass rate by scenario

| Framework | S1 Browse events | S2 Sign-in errors | S3 Buy two seats | S4 Ten-seat limit | S5 Lose a seat to another buyer |
|---|---|---|---|---|---|
| Playwright | 100% | 100% | 100% | 100% | 100% |
| Cypress | 100% | 100% | 100% | 100% | 100% |
| Appium | 100% | 100% | 100% | 100% | 100% |
| Maestro | 100% | 100% | 100% | 100% | 100% |

**Setup** is installing the framework and its browser, driver or CLI on a fresh runner. Building the app and starting the API are shared by every framework on a platform, so they aren't counted. **Test code** counts non-blank, non-comment lines in each suite's tests, helpers and config.

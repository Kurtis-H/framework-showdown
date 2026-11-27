# Results

Measured in GitHub Actions on `ubuntu-latest` (4 cores). Each framework installs from scratch, then runs the whole [test plan](plan/test-plan.md) several times, reseeding the database before each run. Mobile suites run on an Android 14 emulator (API 34, x86_64, 4 cores, 4 GB).

Source: [workflow run 45922842258](https://github.com/Kurtis-H/framework-showdown/actions/runs/45922842258), 10 runs per framework

| Framework | Platform | Setup | Run (median) | Slowest run | Pass rate | All-green runs | Setup + one run | Test code (lines) |
|---|---|---|---|---|---|---|---|---|
| Playwright | Web | 31 s | 3 s | 5 s | 100% | 10 of 10 | 34 s | 97 |
| Cypress | Web | 10 s | 6 s | 16 s | 100% | 10 of 10 | 17 s | 107 |
| Appium | Android | 12 s | 48 s | 58 s | 100% | 10 of 10 | 61 s | 150 |
| Maestro | Android | 13 s | 1.8 min | 1.9 min | 100% | 10 of 10 | 2.0 min | 178 |

## Pass rate by scenario

| Framework | S1 Browse events | S2 Sign-in errors | S3 Buy two seats | S4 Ten-seat limit | S5 Lose a seat to another buyer |
|---|---|---|---|---|---|
| Playwright | 100% | 100% | 100% | 100% | 100% |
| Cypress | 100% | 100% | 100% | 100% | 100% |
| Appium | 100% | 100% | 100% | 100% | 100% |
| Maestro | 100% | 100% | 100% | 100% | 100% |

## Does each suite catch a real bug?

Each app is also built with a planted bug (the order total counts only the first seat), and every suite runs the plan against it once. Only S3, which checks the total, should fail; failing anything else as well would be noise, not a catch.

| Framework | Failed | Verdict |
|---|---|---|
| Playwright | S3 | **caught it** |
| Cypress | S3 | **caught it** |
| Appium | S3 | **caught it** |
| Maestro | S3 | **caught it** |

**Setup** is installing the framework and its browser, driver or CLI on a fresh runner. Building the app and starting the API are shared by every framework on a platform, so they aren't counted. **Test code** counts non-blank, non-comment lines in each suite's tests, helpers and config.

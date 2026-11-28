import { dirname, resolve } from "node:path";

const junitFile = resolve(process.env.JUNIT_FILE ?? "results/junit.xml");

export const config: WebdriverIO.Config = {
  runner: "local",
  tsConfigPath: "./tsconfig.json",
  specs: ["./test/plan.e2e.ts"],
  maxInstances: 1,
  capabilities: [
    {
      platformName: "Android",
      "appium:automationName": "UiAutomator2",
      "appium:deviceName": "emulator-5554",
      "appium:app": resolve(process.env.APK ?? "../../app-profile.apk"),
      "appium:appPackage": "dev.kurtish.booking_mobile",
      "appium:appActivity": ".MainActivity",
      "appium:newCommandTimeout": 240,
      "appium:autoGrantPermissions": true,
      // Don't wait for the app to go "idle" before every command. Flutter apps
      // often never do, and on a Pixel 6 screen UiAutomator2 timed out finding
      // the window at all. Every step already waits for the element it needs.
      "appium:waitForIdleTimeout": 0,
    },
  ],
  // Starts the Appium server from this package's own node_modules.
  services: [["appium", { command: "appium", args: { relaxedSecurity: true } }]],
  logLevel: "warn",
  waitforTimeout: 20_000,
  connectionRetryTimeout: 180_000,
  connectionRetryCount: 1,
  framework: "mocha",
  // Compared run for run with the other frameworks: no retries.
  mochaOpts: { timeout: 180_000, retries: 0 },
  reporters: [
    "spec",
    ["junit", { outputDir: dirname(junitFile), outputFileFormat: () => junitFile.split("/").pop()! }],
  ],
};

// Not a test: the first Appium session on a fresh emulator installs the
// UiAutomator2 server on the device. CI runs this once, untimed, before the
// measured runs, just as Maestro gets a warm-up flow, so neither framework's
// first run pays a one-off cost the others don't.
import { freshApp } from "./app.ts";

describe("warm-up", () => {
  it("opens the app", freshApp);
});

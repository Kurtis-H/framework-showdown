// The shared test plan (plan/test-plan.md) in Appium, against booking-mobile.
import { expect } from "@wdio/globals";
import { BUYER_KEY, button, byId, byText, freshApp, idGone, newEvent, openEvent, rivalBuys, signIn } from "./app.ts";

describe("plan", () => {
  beforeEach(freshApp);

  it("S1 Browse events", async () => {
    await expect(byText("Page 1 of")).toBeDisplayed();
    await button("Next").click();
    await expect(byText("Page 2 of")).toBeDisplayed();
  });

  it("S2 Sign-in errors", async () => {
    await button("Sign in").click();
    const field = await $('android=new UiSelector().resourceId("api-key-field")');
    await field.waitForDisplayed();
    await button("Sign in").click();
    await expect(byText("Enter an API key.")).toBeDisplayed();
    await field.click();
    await field.setValue("key-not-real");
    await driver.hideKeyboard().catch(() => undefined);
    await button("Sign in").click();
    await expect(byText("That API key wasn't recognised.")).toBeDisplayed();
  });

  it("S3 Buy two seats", async () => {
    const event = await newEvent("S3 Buy two seats", 4);
    await signIn(BUYER_KEY);
    await openEvent(event.id);
    await (await byId("seat-S-1")).click();
    await (await byId("seat-S-2")).click();
    await expect(byText("Total: $70.00")).toBeDisplayed();
    await button("Buy 2 seats").click();

    await expect(byText("Thanks! Your order is confirmed.")).toBeDisplayed();
    const title = await byText("Order #").getAttribute("content-desc");
    const order = (title ?? "").match(/Order #\d+/)![0];
    await driver.back();
    await button("My orders").click();
    await expect(byText(order)).toBeDisplayed();
  });

  it("S4 Ten-seat limit", async () => {
    const event = await newEvent("S4 Ten-seat limit", 12);
    await openEvent(event.id);
    for (let n = 1; n <= 11; n++) await (await byId(`seat-S-${n}`)).click();
    await expect(byText("You can buy up to 10 seats in one order.")).toBeDisplayed();
    await expect(byText("Sign in to buy 10 seats")).toBeDisplayed();
  });

  it("S5 Lose a seat to another buyer", async () => {
    const event = await newEvent("S5 Lose a seat", 2);
    await signIn(BUYER_KEY);
    await openEvent(event.id);
    await (await byId("seat-S-1")).click();
    await rivalBuys(event.seatIds[0]);
    await button("Buy 1 seat").click();
    await expect(byText("Someone just took one of those seats")).toBeDisplayed();
    await idGone("seat-S-1");
  });
});

// The shared test plan (plan/test-plan.md) in Playwright, against booking-web.
import { expect, test, type Page } from "@playwright/test";
import { BUYER_KEY, newEvent, rivalBuys } from "./api";

const seat = (page: Page, label: string) => page.getByRole("button", { name: new RegExp(`^Seat ${label},`) });

async function signIn(page: Page, key: string) {
  await page.goto("/signin");
  await page.getByLabel("API key").fill(key);
  await page.getByRole("button", { name: "Sign in" }).click();
  await expect(page.getByRole("button", { name: "Sign out" })).toBeVisible();
}

test("S1 Browse events", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByRole("heading", { name: "Upcoming events" })).toBeVisible();
  await expect(page.getByText(/^Page 1 of \d+$/)).toBeVisible();
  await page.getByRole("button", { name: "Next" }).click();
  await expect(page.getByText(/^Page 2 of \d+$/)).toBeVisible();
});

test("S2 Sign-in errors", async ({ page }) => {
  await page.goto("/signin");
  await page.getByRole("button", { name: "Sign in" }).click();
  await expect(page.getByRole("alert")).toHaveText("Enter an API key.");
  await page.getByLabel("API key").fill("key-not-real");
  await page.getByRole("button", { name: "Sign in" }).click();
  await expect(page.getByRole("alert")).toHaveText("That API key wasn't recognised.");
});

test("S3 Buy two seats", async ({ page }) => {
  const event = await newEvent("S3 Buy two seats", 4);
  await signIn(page, BUYER_KEY);
  await page.goto(`/events/${event.id}`);
  await seat(page, "S-1").click();
  await seat(page, "S-2").click();
  await expect(page.getByTestId("order-total")).toHaveText("$70.00");
  await page.getByRole("button", { name: "Buy 2 seats" }).click();

  await expect(page.getByTestId("order-confirmation")).toBeVisible();
  const order = (await page.getByRole("heading", { level: 1 }).textContent())!.trim();
  await page.getByRole("navigation", { name: "Main" }).getByRole("link", { name: "My orders" }).click();
  await expect(page.getByTestId("order-row").first()).toContainText(order);
});

test("S4 Ten-seat limit", async ({ page }) => {
  const event = await newEvent("S4 Ten-seat limit", 12);
  await page.goto(`/events/${event.id}`);
  for (let n = 1; n <= 11; n++) await seat(page, `S-${n}`).click();
  await expect(page.getByRole("alert")).toHaveText("You can buy up to 10 seats in one order.");
  await expect(page.getByTestId("order-summary").getByRole("listitem")).toHaveCount(10);
});

test("S5 Lose a seat to another buyer", async ({ page }) => {
  const event = await newEvent("S5 Lose a seat", 2);
  await signIn(page, BUYER_KEY);
  await page.goto(`/events/${event.id}`);
  await seat(page, "S-1").click();
  await rivalBuys(event.seatIds[0]);
  await page.getByRole("button", { name: "Buy 1 seat" }).click();
  await expect(page.getByRole("alert")).toContainText("Someone just took one of those seats");
  await expect(seat(page, "S-1")).toHaveCount(0);
});

// Helpers for finding things in the Flutter app. Flutter puts visible text in
// accessibility labels (content-desc), and Semantics(identifier:) becomes the
// Android resource-id, so those are what Appium can see.
const APP_ID = "dev.kurtish.booking_mobile";
const API = process.env.API_URL ?? "http://localhost:8000";

export const BUYER_KEY = "key-user-2";
const RIVAL_KEY = "key-user-3";

/** An element whose label or text contains `text`. */
export const byText = (text: string) =>
  $(`//*[contains(@content-desc, ${xpathString(text)}) or contains(@text, ${xpathString(text)})]`);

/** A button whose label is exactly `label`. */
export const button = (label: string) => $(`//android.widget.Button[@content-desc=${xpathString(label)}]`);

/** An element by its Flutter Semantics identifier, scrolled into view first. */
export async function byId(id: string) {
  const selector = `android=new UiScrollable(new UiSelector().scrollable(true)).scrollIntoView(new UiSelector().resourceId("${id}"))`;
  const scrolled = await $(selector);
  if (await scrolled.isExisting()) return scrolled;
  return $(`android=new UiSelector().resourceId("${id}")`);
}

export const idGone = (id: string) =>
  $(`android=new UiSelector().resourceId("${id}")`).waitForExist({ reverse: true });

function xpathString(s: string) {
  if (!s.includes("'")) return `'${s}'`;
  if (!s.includes('"')) return `"${s}"`;
  return `concat('${s.split("'").join(`', "'", '`)}')`;
}

/** Start every scenario from a freshly cleared app, like Maestro's clearState. */
export async function freshApp() {
  await driver.execute("mobile: clearApp", { appId: APP_ID });
  await driver.activateApp(APP_ID);
  await byText("Upcoming events").waitForDisplayed({ timeout: 60_000 });
}

export async function signIn(key: string) {
  await button("Sign in").click();
  const field = await $('android=new UiSelector().resourceId("api-key-field")');
  await field.waitForDisplayed();
  await field.click();
  await field.setValue(key);
  await driver.hideKeyboard().catch(() => undefined);
  await button("Sign in").click();
  await button("Sign out").waitForDisplayed();
}

/** Fresh events are on page 2 (see plan/test-plan.md). */
export async function openEvent(id: number) {
  await button("Next").click();
  await byText("Page 2 of").waitForDisplayed();
  await (await byId(`event-${id}`)).click();
  await byText("Choose your seats").waitForDisplayed();
}

export async function newEvent(name: string, seats: number, priceCents = 3500) {
  const created = await fetch(`${API}/admin/events`, {
    method: "POST",
    headers: { "X-API-Key": "key-admin", "Content-Type": "application/json" },
    body: JSON.stringify({ name, venue: "Showdown Hall", starts_at: "2027-06-01T19:00:00Z", seats, price_cents: priceCents }),
  });
  if (created.status !== 201) throw new Error(`creating an event: ${created.status} ${await created.text()}`);
  const { id } = (await created.json()) as { id: number };
  const listed = await fetch(`${API}/events/${id}/seats?limit=100`);
  const seatIds = ((await listed.json()) as { items: { id: number }[] }).items.map((s) => s.id);
  return { id, seatIds };
}

export async function rivalBuys(seatId: number) {
  const res = await fetch(`${API}/orders`, {
    method: "POST",
    headers: { "X-API-Key": RIVAL_KEY, "Content-Type": "application/json" },
    body: JSON.stringify({ seat_ids: [seatId] }),
  });
  if (res.status !== 201) throw new Error(`rival order: ${res.status} ${await res.text()}`);
}

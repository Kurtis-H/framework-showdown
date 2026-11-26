// Setup through the booking API, as the plan asks.
const API = process.env.API_URL ?? "http://localhost:8000";

export const BUYER_KEY = "key-user-2";
const RIVAL_KEY = "key-user-3";

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

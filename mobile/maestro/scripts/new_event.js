// Creates an event through the API, as the plan asks. Runs on the machine
// running Maestro, so the API is on localhost here (the app uses 10.0.2.2).
const created = http.post(`${API_URL}/admin/events`, {
  headers: { "X-API-Key": "key-admin", "Content-Type": "application/json" },
  body: JSON.stringify({
    name: NAME,
    venue: "Showdown Hall",
    starts_at: "2027-06-01T19:00:00Z",
    seats: Number(SEATS),
    price_cents: 3500,
  }),
});
if (created.status !== 201) throw new Error(`creating an event: ${created.status} ${created.body}`);
output.eventId = json(created.body).id;
const seats = json(http.get(`${API_URL}/events/${output.eventId}/seats?limit=100`).body);
output.firstSeatId = seats.items[0].id;

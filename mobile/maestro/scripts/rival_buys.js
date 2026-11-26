// Another buyer takes the event's first seat through the API.
const res = http.post(`${API_URL}/orders`, {
  headers: { "X-API-Key": "key-user-3", "Content-Type": "application/json" },
  body: JSON.stringify({ seat_ids: [output.firstSeatId] }),
});
if (res.status !== 201) throw new Error(`rival order: ${res.status} ${res.body}`);

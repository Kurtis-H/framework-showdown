import "@testing-library/cypress/add-commands";

export const BUYER_KEY = "key-user-2";
const RIVAL_KEY = "key-user-3";
const api = () => Cypress.env("API_URL") as string;

// Setup through the booking API, as the plan asks.
export function newEvent(name: string, seats: number, priceCents = 3500) {
  return cy
    .request({
      method: "POST",
      url: `${api()}/admin/events`,
      headers: { "X-API-Key": "key-admin" },
      body: { name, venue: "Showdown Hall", starts_at: "2027-06-01T19:00:00Z", seats, price_cents: priceCents },
    })
    .then((created) => {
      expect(created.status).to.eq(201);
      const id = created.body.id as number;
      return cy.request(`${api()}/events/${id}/seats?limit=100`).then((listed) => ({
        id,
        seatIds: (listed.body.items as { id: number }[]).map((s) => s.id),
      }));
    });
}

export function rivalBuys(seatId: number) {
  return cy
    .request({
      method: "POST",
      url: `${api()}/orders`,
      headers: { "X-API-Key": RIVAL_KEY },
      body: { seat_ids: [seatId] },
    })
    .its("status")
    .should("eq", 201);
}

export function signIn(key: string) {
  cy.visit("/signin");
  cy.findByLabelText("API key").type(key);
  cy.findByRole("button", { name: "Sign in" }).click();
  cy.findByRole("button", { name: "Sign out" }).should("be.visible");
}

export const seat = (label: string) => cy.findByRole("button", { name: new RegExp(`^Seat ${label},`) });

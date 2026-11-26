// The shared test plan (plan/test-plan.md) in Cypress, against booking-web.
import { BUYER_KEY, newEvent, rivalBuys, seat, signIn } from "../support/e2e";

it("S1 Browse events", () => {
  cy.visit("/");
  cy.findByRole("heading", { name: "Upcoming events" }).should("be.visible");
  cy.findByText(/^Page 1 of \d+$/).should("be.visible");
  cy.findByRole("button", { name: "Next" }).click();
  cy.findByText(/^Page 2 of \d+$/).should("be.visible");
});

it("S2 Sign-in errors", () => {
  cy.visit("/signin");
  cy.findByRole("button", { name: "Sign in" }).click();
  cy.findByRole("alert").should("have.text", "Enter an API key.");
  cy.findByLabelText("API key").type("key-not-real");
  cy.findByRole("button", { name: "Sign in" }).click();
  cy.findByRole("alert").should("have.text", "That API key wasn't recognised.");
});

it("S3 Buy two seats", () => {
  newEvent("S3 Buy two seats", 4).then((event) => {
    signIn(BUYER_KEY);
    cy.visit(`/events/${event.id}`);
    seat("S-1").click();
    seat("S-2").click();
    cy.findByTestId("order-total").should("have.text", "$70.00");
    cy.findByRole("button", { name: "Buy 2 seats" }).click();

    cy.findByTestId("order-confirmation").should("be.visible");
    cy.findByRole("heading", { level: 1 })
      .invoke("text")
      .then((order) => {
        cy.findByRole("navigation", { name: "Main" }).findByRole("link", { name: "My orders" }).click();
        cy.findAllByTestId("order-row").first().should("contain.text", order.trim());
      });
  });
});

it("S4 Ten-seat limit", () => {
  newEvent("S4 Ten-seat limit", 12).then((event) => {
    cy.visit(`/events/${event.id}`);
    for (let n = 1; n <= 11; n++) seat(`S-${n}`).click();
    cy.findByRole("alert").should("have.text", "You can buy up to 10 seats in one order.");
    cy.findByTestId("order-summary").findAllByRole("listitem").should("have.length", 10);
  });
});

it("S5 Lose a seat to another buyer", () => {
  newEvent("S5 Lose a seat", 2).then((event) => {
    signIn(BUYER_KEY);
    cy.visit(`/events/${event.id}`);
    seat("S-1").click();
    rivalBuys(event.seatIds[0]);
    cy.findByRole("button", { name: "Buy 1 seat" }).click();
    cy.findByRole("alert").should("contain.text", "Someone just took one of those seats");
    seat("S-1").should("not.exist");
  });
});

import { dirname } from "node:path";
import { defineConfig } from "cypress";

// Cypress writes one JUnit file per spec; [hash] keeps them apart.
const junitDir = dirname(process.env.JUNIT_FILE ?? "results/junit.xml");

export default defineConfig({
  e2e: {
    baseUrl: process.env.WEB_URL ?? "http://localhost:4173",
    specPattern: "cypress/e2e/**/*.cy.ts",
    supportFile: "cypress/support/e2e.ts",
  },
  env: { API_URL: process.env.API_URL ?? "http://localhost:8000" },
  // Compared run for run with the other frameworks: no retries, no video.
  retries: 0,
  video: false,
  screenshotOnRunFailure: true,
  reporter: "junit",
  reporterOptions: { mochaFile: `${junitDir}/junit-[hash].xml`, toConsole: false },
});

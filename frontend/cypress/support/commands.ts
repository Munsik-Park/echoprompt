/// <reference types="cypress" />

declare global {
  namespace Cypress {
    interface Chainable {
      /**
       * Custom command to create a new session
       * @example cy.createSession('Test Session')
       */
      createSession(name: string): Chainable<void>
      
      /**
       * Custom command to delete a session
       * @example cy.deleteSession(123)
       */
      deleteSession(id: number): Chainable<void>
    }
  }
}

// 환경 변수 체크
if (!Cypress.env('apiUrl')) {
  throw new Error('API URL environment variable is not set');
}

const API_URL = Cypress.env('apiUrl');
if (!API_URL) {
  throw new Error('apiUrl environment variable is not set');
}

const API_VERSION = Cypress.env('apiVersion');
if (!API_VERSION) {
  throw new Error('apiVersion environment variable is not set');
}

Cypress.Commands.add('createSession', (name: string) => {
  cy.get('[data-testid="new-session-button"]').click();
  cy.get('[data-testid="session-name-input"]').type(name);
  cy.get('[data-testid="create-session-button"]').click();
});

Cypress.Commands.add('deleteSession', (id: number) => {
  cy.request({
    method: 'DELETE',
    url: `${API_URL}/api/${API_VERSION}/sessions/${id}`,
    failOnStatusCode: false
  });
});

export {}; 
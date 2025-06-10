import { Page } from '@playwright/test';

export async function waitForHighlight(page: Page, messageText: string) {
  await page.waitForFunction(
    (text) => {
      const nodes = Array.from(document.querySelectorAll('[data-testid^="message-"]'));
      return nodes.some(node => node.textContent?.includes(text) && node.classList.contains('highlighted-message'));
    },
    messageText,
    { timeout: 10000 }
  );
}

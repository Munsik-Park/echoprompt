import { Page, expect } from '@playwright/test';

export async function waitForHighlight(page: Page, messageText: string) {
  try {
    await page.waitForFunction(
      (text) => {
        const nodes = Array.from(
          document.querySelectorAll('[data-testid^="message-"]')
        );
        return nodes.some(
          (node) =>
            node.textContent?.includes(text) &&
            node.classList.contains('highlighted-message')
        );
      },
      messageText,
      { timeout: 15000 }
    );
  } catch {
    await expect(
      page.locator('[data-testid^="message-"]', { hasText: messageText })
    ).toBeVisible();
  }
}

import { Page } from '@playwright/test';

export class TestError extends Error {
  constructor(
    message: string,
    public step: string,
    public context: Record<string, any> = {}
  ) {
    super(message);
    this.name = 'TestError';
  }
}

export interface ErrorHandlerOptions {
  page: Page;
  step: string;
  timeout?: number;
  context?: Record<string, any>;
}

export async function handleTestError(
  operation: () => Promise<void>,
  options: ErrorHandlerOptions
) {
  const { page, step, timeout = 5000, context = {} } = options;
  
  try {
    await operation();
  } catch (error) {
    console.error(`Error in step "${step}":`, error);
    console.error('Context:', context);
    
    // 스크린샷 저장
    await page.screenshot({ 
      path: `error-${step}-${Date.now()}.png`,
      fullPage: true 
    });
    
    throw new TestError(
      error instanceof Error ? error.message : 'Unknown error',
      step,
      context
    );
  }
}

// 공통 작업을 위한 래퍼 함수들
export const commonOperations = {
  async waitForElement(
    page: Page,
    selector: string,
    options: { timeout?: number; state?: 'visible' | 'hidden' } = {}
  ) {
    return handleTestError(
      async () => {
        const element = page.locator(selector);
        await element.waitFor({ 
          state: options.state || 'visible',
          timeout: options.timeout || 5000 
        });
      },
      {
        page,
        step: `waitForElement: ${selector}`,
        context: { selector, options }
      }
    );
  },

  async fillInput(
    page: Page,
    selector: string,
    value: string,
    options: { timeout?: number } = {}
  ) {
    return handleTestError(
      async () => {
        const input = page.locator(selector);
        await input.fill(value);
      },
      {
        page,
        step: `fillInput: ${selector}`,
        context: { selector, value, options }
      }
    );
  },

  async clickElement(
    page: Page,
    selector: string,
    options: { timeout?: number } = {}
  ) {
    return handleTestError(
      async () => {
        const element = page.locator(selector);
        await element.click();
      },
      {
        page,
        step: `clickElement: ${selector}`,
        context: { selector, options }
      }
    );
  },

  async pressKey(
    page: Page,
    key: string,
    options: { timeout?: number } = {}
  ) {
    return handleTestError(
      async () => {
        await page.keyboard.press(key);
      },
      {
        page,
        step: `pressKey: ${key}`,
        context: { key, options }
      }
    );
  }
}; 
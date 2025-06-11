import { Page, TestInfo } from '@playwright/test';
import { handleTestError } from './errorHandler';
import { logger } from './logger';
import { metricsCollector } from './metrics';
import { pluginManager } from './plugins';
import { createSession, selectSession } from './sessionManager';

export interface TestCaseOptions {
  name: string;
  description?: string;
  timeout?: number;
  retries?: number;
  tags?: string[];
  dependencies?: string[];
}

export interface TestContext {
  testInfo: TestInfo;
  apiContext: any;
  sessionId?: number;
  metadata: Record<string, any>;
}

export interface TestCase {
  options: TestCaseOptions;
  setup: (page: Page, context: TestContext) => Promise<void>;
  execute: (page: Page, context: TestContext) => Promise<void>;
  verify: (page: Page, context: TestContext) => Promise<void>;
  cleanup?: (page: Page, context: TestContext) => Promise<void>;
}

export async function runTestCase(page: Page, testCase: TestCase, context: TestContext) {
  const { options } = testCase;
  
  try {
    logger.info(`테스트 케이스 시작: ${options.name}`, { 
      testName: options.name,
      description: options.description,
      tags: options.tags 
    });

    metricsCollector.startTest(options.name, {
      description: options.description,
      tags: options.tags,
      dependencies: options.dependencies
    });

    await pluginManager.onTestStart(testCase);

    // 1. 테스트 설정
    metricsCollector.startStep(options.name, 'setup');
    await pluginManager.onStepStart(testCase, 'setup');
    await handleTestError(
      async () => {
        await testCase.setup(page, context);
      },
      {
        page,
        step: 'setup',
        context: { testName: options.name }
      }
    );
    metricsCollector.endStep(options.name, 'passed');
    await pluginManager.onStepEnd(testCase, 'setup', 'passed');

    // 2. 테스트 실행
    metricsCollector.startStep(options.name, 'execute');
    await pluginManager.onStepStart(testCase, 'execute');
    await handleTestError(
      async () => {
        await testCase.execute(page, context);
      },
      {
        page,
        step: 'execute',
        context: { testName: options.name }
      }
    );
    metricsCollector.endStep(options.name, 'passed');
    await pluginManager.onStepEnd(testCase, 'execute', 'passed');

    // 3. 테스트 검증
    metricsCollector.startStep(options.name, 'verify');
    await pluginManager.onStepStart(testCase, 'verify');
    await handleTestError(
      async () => {
        await testCase.verify(page, context);
      },
      {
        page,
        step: 'verify',
        context: { testName: options.name }
      }
    );
    metricsCollector.endStep(options.name, 'passed');
    await pluginManager.onStepEnd(testCase, 'verify', 'passed');

    // 4. 테스트 정리
    if (testCase.cleanup) {
      metricsCollector.startStep(options.name, 'cleanup');
      await pluginManager.onStepStart(testCase, 'cleanup');
      await handleTestError(
        async () => {
          await testCase.cleanup!(page, context);
        },
        {
          page,
          step: 'cleanup',
          context: { testName: options.name }
        }
      );
      metricsCollector.endStep(options.name, 'passed');
      await pluginManager.onStepEnd(testCase, 'cleanup', 'passed');
    }

    metricsCollector.endTest(options.name, 'passed');
    await pluginManager.onTestEnd(testCase, {
      status: 'passed',
      metrics: metricsCollector.getMetrics(options.name)!
    });

    logger.info(`테스트 케이스 완료: ${options.name}`, { 
      testName: options.name,
      status: 'passed'
    });

  } catch (error) {
    const currentStep = metricsCollector.getMetrics(options.name)?.steps.slice(-1)[0];
    if (currentStep) {
      metricsCollector.endStep(options.name, 'failed', error as Error);
      await pluginManager.onStepEnd(testCase, currentStep.name, 'failed');
    }

    metricsCollector.endTest(options.name, 'failed', error as Error);
    await pluginManager.onTestEnd(testCase, {
      status: 'failed',
      error: error as Error,
      metrics: metricsCollector.getMetrics(options.name)!
    });

    logger.error(error as Error, { 
      testName: options.name,
      step: currentStep?.name
    });

    throw error;
  }
}

export async function setupTestEnvironment(env: TestContext) {
  const { page, apiContext, testInfo } = env;
  
  return handleTestError(
    async () => {
      // 1. 페이지 로드
      await page.goto(process.env.VITE_FRONTEND_URL as string);
      await page.waitForLoadState('networkidle');
      logger.info('페이지 로드 완료');
      
      // 2. 세션 생성 및 선택
      const session = await createSession(apiContext, testInfo.title);
      await page.waitForTimeout(1500);
      await page.reload();
      await page.waitForTimeout(1000);
      
      const sessionItems = page.locator('[data-testid="session-item"]');
      const sessionCount = await sessionItems.count();
      if (sessionCount === 0) {
        throw new Error('세션 생성 실패로 테스트를 중단합니다.');
      }
      
      await selectSession(page, session.id);
      logger.info('테스트 환경 설정 완료');

      return {
        ...env,
        sessionId: session.id
      };
    },
    {
      page,
      step: 'setupTestEnvironment',
      context: { testInfo }
    }
  );
} 
import { logger } from './logger';

export interface TestStep {
  name: string;
  startTime: number;
  endTime?: number;
  duration?: number;
  status: 'passed' | 'failed' | 'skipped';
  error?: Error;
}

export interface TestMetrics {
  testName: string;
  startTime: number;
  endTime?: number;
  duration?: number;
  status: 'passed' | 'failed' | 'skipped';
  error?: Error;
  steps: TestStep[];
  metadata: Record<string, any>;
}

class MetricsCollector {
  private metrics: Map<string, TestMetrics> = new Map();
  private currentStep?: TestStep;

  startTest(testName: string, metadata: Record<string, any> = {}): void {
    this.metrics.set(testName, {
      testName,
      startTime: Date.now(),
      status: 'passed',
      steps: [],
      metadata
    });
    logger.info(`Test started: ${testName}`, { testName, metadata });
  }

  endTest(testName: string, status: 'passed' | 'failed' | 'skipped', error?: Error): void {
    const test = this.metrics.get(testName);
    if (!test) {
      logger.warn(`No metrics found for test: ${testName}`);
      return;
    }

    test.endTime = Date.now();
    test.duration = test.endTime - test.startTime;
    test.status = status;
    test.error = error;

    logger.info(`Test ended: ${testName}`, {
      testName,
      status,
      duration: test.duration,
      error: error?.message
    });
  }

  startStep(testName: string, stepName: string): void {
    const test = this.metrics.get(testName);
    if (!test) {
      logger.warn(`No metrics found for test: ${testName}`);
      return;
    }

    this.currentStep = {
      name: stepName,
      startTime: Date.now(),
      status: 'passed'
    };

    test.steps.push(this.currentStep);
    logger.debug(`Step started: ${stepName}`, { testName, stepName });
  }

  endStep(testName: string, status: 'passed' | 'failed' | 'skipped', error?: Error): void {
    if (!this.currentStep) {
      logger.warn(`No current step found for test: ${testName}`);
      return;
    }

    this.currentStep.endTime = Date.now();
    this.currentStep.duration = this.currentStep.endTime - this.currentStep.startTime;
    this.currentStep.status = status;
    this.currentStep.error = error;

    logger.debug(`Step ended: ${this.currentStep.name}`, {
      testName,
      stepName: this.currentStep.name,
      status,
      duration: this.currentStep.duration,
      error: error?.message
    });

    this.currentStep = undefined;
  }

  getMetrics(testName: string): TestMetrics | undefined {
    return this.metrics.get(testName);
  }

  getAllMetrics(): TestMetrics[] {
    return Array.from(this.metrics.values());
  }

  clearMetrics(): void {
    this.metrics.clear();
    this.currentStep = undefined;
  }
}

export const metricsCollector = new MetricsCollector(); 
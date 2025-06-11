import { Page } from '@playwright/test';
import { logger } from './logger';
import { TestMetrics } from './metrics';
import { TestCase } from './testCase';

export interface TestResult {
  status: 'passed' | 'failed' | 'skipped';
  error?: Error;
  metrics: TestMetrics;
}

export interface TestPlugin {
  name: string;
  setup?: () => Promise<void>;
  teardown?: () => Promise<void>;
  onTestStart?: (test: TestCase) => Promise<void>;
  onTestEnd?: (test: TestCase, result: TestResult) => Promise<void>;
  onStepStart?: (test: TestCase, stepName: string) => Promise<void>;
  onStepEnd?: (test: TestCase, stepName: string, status: 'passed' | 'failed' | 'skipped') => Promise<void>;
  onError?: (error: Error, context: Record<string, any>) => Promise<void>;
}

class PluginManager {
  private plugins: Map<string, TestPlugin> = new Map();

  register(plugin: TestPlugin): void {
    if (this.plugins.has(plugin.name)) {
      logger.warn(`Plugin ${plugin.name} is already registered`);
      return;
    }
    this.plugins.set(plugin.name, plugin);
    logger.info(`Plugin registered: ${plugin.name}`);
  }

  async setup(): Promise<void> {
    for (const plugin of this.plugins.values()) {
      if (plugin.setup) {
        try {
          await plugin.setup();
          logger.info(`Plugin setup completed: ${plugin.name}`);
        } catch (error) {
          logger.error(error as Error, { plugin: plugin.name, step: 'setup' });
        }
      }
    }
  }

  async teardown(): Promise<void> {
    for (const plugin of this.plugins.values()) {
      if (plugin.teardown) {
        try {
          await plugin.teardown();
          logger.info(`Plugin teardown completed: ${plugin.name}`);
        } catch (error) {
          logger.error(error as Error, { plugin: plugin.name, step: 'teardown' });
        }
      }
    }
  }

  async onTestStart(test: TestCase): Promise<void> {
    for (const plugin of this.plugins.values()) {
      if (plugin.onTestStart) {
        try {
          await plugin.onTestStart(test);
        } catch (error) {
          logger.error(error as Error, { 
            plugin: plugin.name, 
            step: 'onTestStart',
            test: test.options.name 
          });
        }
      }
    }
  }

  async onTestEnd(test: TestCase, result: TestResult): Promise<void> {
    for (const plugin of this.plugins.values()) {
      if (plugin.onTestEnd) {
        try {
          await plugin.onTestEnd(test, result);
        } catch (error) {
          logger.error(error as Error, { 
            plugin: plugin.name, 
            step: 'onTestEnd',
            test: test.options.name 
          });
        }
      }
    }
  }

  async onStepStart(test: TestCase, stepName: string): Promise<void> {
    for (const plugin of this.plugins.values()) {
      if (plugin.onStepStart) {
        try {
          await plugin.onStepStart(test, stepName);
        } catch (error) {
          logger.error(error as Error, { 
            plugin: plugin.name, 
            step: 'onStepStart',
            test: test.options.name,
            stepName 
          });
        }
      }
    }
  }

  async onStepEnd(
    test: TestCase, 
    stepName: string, 
    status: 'passed' | 'failed' | 'skipped'
  ): Promise<void> {
    for (const plugin of this.plugins.values()) {
      if (plugin.onStepEnd) {
        try {
          await plugin.onStepEnd(test, stepName, status);
        } catch (error) {
          logger.error(error as Error, { 
            plugin: plugin.name, 
            step: 'onStepEnd',
            test: test.options.name,
            stepName,
            status 
          });
        }
      }
    }
  }

  async onError(error: Error, context: Record<string, any>): Promise<void> {
    for (const plugin of this.plugins.values()) {
      if (plugin.onError) {
        try {
          await plugin.onError(error, context);
        } catch (pluginError) {
          logger.error(pluginError as Error, { 
            plugin: plugin.name, 
            step: 'onError',
            originalError: error.message 
          });
        }
      }
    }
  }
}

export const pluginManager = new PluginManager(); 
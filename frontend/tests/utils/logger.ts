import { testConfig } from '../config/test.config';

export interface LogContext {
  testName?: string;
  step?: string;
  [key: string]: any;
}

export interface TestLogger {
  info(message: string, context?: LogContext): void;
  error(error: Error, context?: LogContext): void;
  debug(message: string, context?: LogContext): void;
  warn(message: string, context?: LogContext): void;
}

class Logger implements TestLogger {
  private formatMessage(level: string, message: string, context?: LogContext): string {
    const timestamp = new Date().toISOString();
    const contextStr = context ? ` ${JSON.stringify(context)}` : '';
    return `[${timestamp}] ${level}: ${message}${contextStr}`;
  }

  private shouldLog(level: string): boolean {
    const levels = ['debug', 'info', 'warn', 'error'];
    const configLevel = levels.indexOf(testConfig.logLevel);
    const messageLevel = levels.indexOf(level);
    return messageLevel >= configLevel;
  }

  info(message: string, context?: LogContext): void {
    if (this.shouldLog('info')) {
      console.log(this.formatMessage('INFO', message, context));
    }
  }

  error(error: Error, context?: LogContext): void {
    if (this.shouldLog('error')) {
      console.error(this.formatMessage('ERROR', error.message, {
        ...context,
        stack: error.stack
      }));
    }
  }

  debug(message: string, context?: LogContext): void {
    if (this.shouldLog('debug')) {
      console.debug(this.formatMessage('DEBUG', message, context));
    }
  }

  warn(message: string, context?: LogContext): void {
    if (this.shouldLog('warn')) {
      console.warn(this.formatMessage('WARN', message, context));
    }
  }
}

export const logger = new Logger(); 
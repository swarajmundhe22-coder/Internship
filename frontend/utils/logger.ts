import { v4 as uuidv4 } from 'uuid';

export enum LogLevel {
  TRACE = 0,
  DEBUG = 1,
  INFO = 2,
  WARN = 3,
  ERROR = 4,
  FATAL = 5,
}

interface LogEntry {
  timestamp: string;
  level: string;
  correlation_id: string;
  message: string;
  context?: Record<string, any>;
  error?: any;
}

class Logger {
  private correlationId: string;
  private minLevel: LogLevel = LogLevel.INFO;

  constructor() {
    this.correlationId = uuidv4();
  }

  setCorrelationId(id: string) {
    this.correlationId = id;
  }

  getCorrelationId() {
    return this.correlationId;
  }

  private formatEntry(level: LogLevel, message: string, context?: Record<string, any>, error?: any): LogEntry {
    return {
      timestamp: new Date().toISOString(),
      level: LogLevel[level],
      correlation_id: this.correlationId,
      message,
      context,
      error: error instanceof Error ? { name: error.name, message: error.message, stack: error.stack } : error,
    };
  }

  private log(level: LogLevel, message: string, context?: Record<string, any>, error?: any) {
    if (level < this.minLevel) return;

    const entry = this.formatEntry(level, message, context, error);
    const logMethod = level >= LogLevel.ERROR ? 'error' : level >= LogLevel.WARN ? 'warn' : 'log';
    
    // In production, this would be shipped to a centralized SIEM like Datadog or ELK
    console[logMethod](JSON.stringify(entry));
  }

  trace(message: string, context?: Record<string, any>) { this.log(LogLevel.TRACE, message, context); }
  debug(message: string, context?: Record<string, any>) { this.log(LogLevel.DEBUG, message, context); }
  info(message: string, context?: Record<string, any>) { this.log(LogLevel.INFO, message, context); }
  warn(message: string, context?: Record<string, any>) { this.log(LogLevel.WARN, message, context); }
  error(message: string, context?: Record<string, any>, error?: any) { this.log(LogLevel.ERROR, message, context, error); }
  fatal(message: string, context?: Record<string, any>, error?: any) { this.log(LogLevel.FATAL, message, context, error); }
}

export const logger = new Logger();

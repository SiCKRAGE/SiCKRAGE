import { EventProcessor, Hub, Integration } from '@sentry/types';
/** JSDoc */
interface Report {
    [key: string]: any;
    type: ReportTypes;
    url: string;
    body?: ReportBody;
}
/** JSDoc */
declare enum ReportTypes {
    /** JSDoc */
    Crash = "crash",
    /** JSDoc */
    Deprecation = "deprecation",
    /** JSDoc */
    Intervention = "intervention"
}
/** JSDoc */
declare type ReportBody = CrashReportBody | DeprecationReportBody | InterventionReportBody;
/** JSDoc */
interface CrashReportBody {
    [key: string]: any;
    crashId: string;
    reason?: string;
}
/** JSDoc */
interface DeprecationReportBody {
    [key: string]: any;
    id: string;
    anticipatedRemoval?: Date;
    message: string;
    sourceFile?: string;
    lineNumber?: number;
    columnNumber?: number;
}
/** JSDoc */
interface InterventionReportBody {
    [key: string]: any;
    id: string;
    message: string;
    sourceFile?: string;
    lineNumber?: number;
    columnNumber?: number;
}
/** Reporting API integration - https://w3c.github.io/reporting/ */
export declare class ReportingObserver implements Integration {
    private readonly _options;
    /**
     * @inheritDoc
     */
    readonly name: string;
    /**
     * @inheritDoc
     */
    static id: string;
    /**
     * Returns current hub.
     */
    private _getCurrentHub?;
    /**
     * @inheritDoc
     */
    constructor(_options?: {
        types?: ReportTypes[];
    });
    /**
     * @inheritDoc
     */
    setupOnce(_: (callback: EventProcessor) => void, getCurrentHub: () => Hub): void;
    /**
     * @inheritDoc
     */
    handler(reports: Report[]): void;
}
export {};

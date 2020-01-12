import { EventProcessor, Hub, Integration } from '@sentry/types';
/** Send Console API calls as Sentry Events */
export declare class CaptureConsole implements Integration {
    /**
     * @inheritDoc
     */
    name: string;
    /**
     * @inheritDoc
     */
    static id: string;
    /**
     * @inheritDoc
     */
    private readonly _levels;
    /**
     * @inheritDoc
     */
    constructor(options?: {
        levels?: string[];
    });
    /**
     * @inheritDoc
     */
    setupOnce(_: (callback: EventProcessor) => void, getCurrentHub: () => Hub): void;
}

import { setupWorker } from 'msw/browser';
import { handlers } from './handlers';

// ============================================================================
// MSW Browser Worker - For development in browser
// ============================================================================

export const worker = setupWorker(...handlers);
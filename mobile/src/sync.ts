// The sync engine: drain the offline queue, then pull. Push is idempotent
// by op_id on both ends, so a retry after a dropped connection files
// nothing twice. Rejected ops stay queued and surface to the caller.

import type { TopicSummary } from './types';
import type { SyncTransport } from './transport';
import { dropAccepted, peekQueue } from './queue';

export interface SyncReport {
  pushed: number;
  rejected: { op_id: string; error: string }[];
  pulled: number;
  cursor: string | null;
  topics: TopicSummary[];
}

export async function syncNow(
  transport: SyncTransport,
  cursor: string | null,
): Promise<SyncReport> {
  const queued = await peekQueue();
  let rejected: { op_id: string; error: string }[] = [];
  if (queued.length) {
    const res = await transport.push(queued);
    await dropAccepted(res.accepted);
    rejected = res.rejected;
  }
  const page = await transport.pull(cursor ?? undefined);
  const topics = await transport.topics();
  return {
    pushed: queued.length,
    rejected,
    pulled: page.ops.length,
    cursor: page.cursor,
    topics,
  };
}

// SyncTransport: the seam between the sync engine and the outside world.
// MockTransport keeps the whole app usable before the backend exists and
// gives every screen something deterministic to render in development.

import type { Device, Op, StoredOp, TopicSummary } from './types';
import { TrailmarkApi } from './api';

export interface SyncTransport {
  push(ops: Op[]): Promise<{ accepted: string[]; rejected: { op_id: string; error: string }[] }>;
  pull(cursor?: string): Promise<{ ops: StoredOp[]; cursor: string }>;
  topics(): Promise<TopicSummary[]>;
  devices(): Promise<Device[]>;
  revokeDevice(deviceId: string): Promise<void>;
}

export class HttpTransport implements SyncTransport {
  constructor(private api: TrailmarkApi) {}

  push(ops: Op[]) {
    return this.api.push(ops);
  }

  pull(cursor?: string) {
    return this.api.pull(cursor);
  }

  async topics(): Promise<TopicSummary[]> {
    return (await this.api.topicsSummary()).topics;
  }

  async devices(): Promise<Device[]> {
    return (await this.api.devices()).devices;
  }

  async revokeDevice(deviceId: string): Promise<void> {
    await this.api.revokeDevice(deviceId);
  }
}

// In-memory backend behind the same interface. Topics/entries created here
// are the sample data the app shows before first sync; the op shapes are the
// real contract shapes, so screens built on this need no changes later.
export class MockTransport implements SyncTransport {
  private log: StoredOp[] = [];
  private cursor = 0;

  private append(op: Op): StoredOp {
    const stored: StoredOp = { ...op, applied_at: new Date().toISOString() };
    this.log.push(stored);
    return stored;
  }

  async push(ops: Op[]) {
    const accepted: string[] = [];
    for (const op of ops) {
      if (!this.log.some((s) => s.op_id === op.op_id)) this.append(op);
      accepted.push(op.op_id);
    }
    return { accepted, rejected: [] };
  }

  async pull(cursor?: string) {
    const from = cursor ? parseInt(cursor, 10) || 0 : 0;
    const ops = this.log.slice(from);
    return { ops, cursor: String(this.log.length) };
  }

  async topics(): Promise<TopicSummary[]> {
    const byTopic = new Map<string, StoredOp[]>();
    for (const op of this.log) {
      if (op.op === 'delete') continue;
      const key =
        op.entity === 'topic'
          ? op.entity_id
          : String((op.payload as Record<string, unknown>).topic_id ?? '');
      if (!key) continue;
      const arr = byTopic.get(key) ?? [];
      arr.push(op);
      byTopic.set(key, arr);
    }
    const out: TopicSummary[] = [];
    for (const [topicId, ops] of byTopic) {
      const topic = ops.find((o) => o.entity === 'topic');
      const title =
        topic && typeof (topic.payload as Record<string, unknown>).title === 'string'
          ? String((topic.payload as Record<string, unknown>).title)
          : 'Untitled';
      const entries = ops.filter((o) => o.entity === 'entry').length;
      out.push({
        topic_id: topicId,
        title,
        status: 'open',
        points: entries,
        sources: 0,
        first_at: ops[0]?.client_at ?? '',
        last_at: ops[ops.length - 1]?.client_at ?? '',
      });
    }
    return out;
  }

  async devices(): Promise<Device[]> {
    return [];
  }

  async revokeDevice(_deviceId: string): Promise<void> {}
}

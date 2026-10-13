// Mirrors api/openapi.yaml v1.0.0. Field names match the contract exactly;
// nothing here renames a wire field.

export type EntityKind = 'topic' | 'entry' | 'source' | 'subtopic';
export type OpKind = 'upsert' | 'delete';
export type EntryKind = 'claim' | 'note' | 'quote';

export interface Op {
  op_id: string;
  device_id: string;
  seq: number;
  entity: EntityKind;
  entity_id: string;
  op: OpKind;
  payload: Record<string, unknown>;
  client_at: string;
}

export interface StoredOp extends Op {
  applied_at: string;
}

export interface TopicPayload {
  title: string;
  status: 'open' | 'closed';
}

export interface EntryPayload {
  topic_id: string;
  subtopic: string;
  text: string;
  kind: EntryKind;
}

export interface SourcePayload {
  entry_id: string;
  type: 'link' | 'string' | 'image';
  value: string;
  note?: string;
  attachment_id?: string;
}

export interface Device {
  id: string;
  name: string;
  paired_at: string;
  last_seen_at?: string;
}

export interface TopicSummary {
  topic_id: string;
  title: string;
  status: 'open' | 'closed';
  points: number;
  sources: number;
  first_at: string;
  last_at: string;
}

export interface Session {
  accessToken: string;
  refreshToken: string;
  userId: string;
  email: string;
  deviceId: string | null;
}

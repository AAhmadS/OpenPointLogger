// Offline-first op queue. Every capture lands here first and drains through
// the transport when online - a point is never lost to a tunnel. Backed by
// AsyncStorage so the queue survives process death.

import AsyncStorage from '@react-native-async-storage/async-storage';
import type { Op } from './types';

const QUEUE_KEY = 'trailmark.opqueue.v1';
const SEQ_KEY = 'trailmark.opseq.v1';

function uuid(): string {
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, (c) => {
    const r = Math.floor(Math.random() * 16);
    const v = c === 'x' ? r : (r & 0x3) | 0x8;
    return v.toString(16);
  });
}

export async function nextSeq(): Promise<number> {
  const raw = await AsyncStorage.getItem(SEQ_KEY);
  const next = (raw ? parseInt(raw, 10) || 0 : 0) + 1;
  await AsyncStorage.setItem(SEQ_KEY, String(next));
  return next;
}

export function newOpId(): string {
  return uuid();
}

export async function enqueue(op: Op): Promise<void> {
  const raw = await AsyncStorage.getItem(QUEUE_KEY);
  const ops: Op[] = raw ? (JSON.parse(raw) as Op[]) : [];
  ops.push(op);
  await AsyncStorage.setItem(QUEUE_KEY, JSON.stringify(ops));
}

export async function peekQueue(): Promise<Op[]> {
  const raw = await AsyncStorage.getItem(QUEUE_KEY);
  return raw ? (JSON.parse(raw) as Op[]) : [];
}

export async function dropAccepted(accepted: string[]): Promise<void> {
  if (!accepted.length) return;
  const keep = (await peekQueue()).filter((o) => !accepted.includes(o.op_id));
  await AsyncStorage.setItem(QUEUE_KEY, JSON.stringify(keep));
}

export async function queueLength(): Promise<number> {
  return (await peekQueue()).length;
}

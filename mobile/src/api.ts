// Typed HTTP client for api/openapi.yaml. fetch only, no dependencies, so
// it runs in Expo Go, dev clients and Node alike. Every method throws
// ApiError (message only - tokens and codes never leak into errors).

import type { Device, Op, StoredOp, TopicSummary } from './types';

export class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

interface PushResult {
  accepted: string[];
  rejected: { op_id: string; error: string }[];
}

interface PullResult {
  ops: StoredOp[];
  cursor: string;
}

export class TrailmarkApi {
  constructor(
    private baseUrl: string,
    private getToken: () => Promise<string | null>,
  ) {}

  private async call<T>(path: string, init?: RequestInit): Promise<T> {
    const token = await this.getToken();
    const res = await fetch(this.baseUrl + path, {
      ...init,
      headers: {
        'Content-Type': 'application/json',
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
        ...(init?.headers ?? {}),
      },
    });
    let body: unknown = null;
    try {
      body = await res.json();
    } catch {
      body = null;
    }
    if (!res.ok) {
      const msg =
        typeof body === 'object' && body !== null && 'error' in body
          ? String((body as { error: unknown }).error)
          : `Request failed (${res.status})`;
      throw new ApiError(res.status, msg);
    }
    return body as T;
  }

  // Auth (no token yet - getToken returns null until verified).
  otpRequest(email: string): Promise<{ ok: boolean }> {
    return this.call('/auth/otp/request', {
      method: 'POST',
      body: JSON.stringify({ email }),
    });
  }

  otpVerify(email: string, code: string): Promise<{
    access_token: string;
    refresh_token: string;
    user: { id: string; email: string };
  }> {
    return this.call('/auth/otp/verify', {
      method: 'POST',
      body: JSON.stringify({ email, code }),
    });
  }

  account(): Promise<{
    id: string;
    email: string;
    plan: string;
    devices: Device[];
  }> {
    return this.call('/account');
  }

  pair(code: string, name: string): Promise<{
    device_id: string;
    device_token: string;
    paired_at: string;
  }> {
    return this.call('/devices/pair', {
      method: 'POST',
      body: JSON.stringify({ code, name }),
    });
  }

  devices(): Promise<{ devices: Device[] }> {
    return this.call('/devices');
  }

  revokeDevice(deviceId: string): Promise<{ ok: boolean }> {
    return this.call(`/devices/${encodeURIComponent(deviceId)}`, {
      method: 'DELETE',
    });
  }

  push(ops: Op[]): Promise<PushResult> {
    return this.call('/sync/push', {
      method: 'POST',
      body: JSON.stringify({ ops }),
    });
  }

  pull(cursor?: string, limit = 200): Promise<PullResult> {
    const q = new URLSearchParams({ limit: String(limit) });
    if (cursor) q.set('cursor', cursor);
    return this.call(`/sync/pull?${q.toString()}`);
  }

  uploadUrl(sha256: string, bytes: number, mime: string): Promise<{
    attachment_id: string;
    url: string;
    expires_at: string;
  }> {
    return this.call('/attachments/upload-url', {
      method: 'POST',
      body: JSON.stringify({ sha256, bytes, mime }),
    });
  }

  topicsSummary(): Promise<{ topics: TopicSummary[] }> {
    return this.call('/topics/summary');
  }
}

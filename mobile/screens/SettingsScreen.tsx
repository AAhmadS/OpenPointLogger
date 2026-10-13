// M5 Settings / Account: plan, this device, other devices + revoke, API
// endpoint, theme note, sign out. Billing portal link is intentionally
// absent - T19 is blocked, and dead links are worse than missing ones.

import React, { useState } from 'react';
import { Button, FlatList, StyleSheet, Text, TextInput, View } from 'react-native';
import type { Device } from '../src/types';
import type { SyncTransport } from '../src/transport';
import { queueLength } from '../src/queue';

interface Props {
  email: string;
  plan: string;
  deviceId: string | null;
  devices: Device[];
  transport: SyncTransport;
  apiUrl: string;
  onApiUrl: (url: string) => void;
  queued: number;
  onRefresh: () => void;
  onSignOut: () => void;
}

export default function SettingsScreen({
  email,
  plan,
  deviceId,
  devices,
  transport,
  apiUrl,
  onApiUrl,
  queued,
  onRefresh,
  onSignOut,
}: Props) {
  const [url, setUrl] = useState(apiUrl);
  const [status, setStatus] = useState('');

  async function revoke(id: string) {
    try {
      await transport.revokeDevice(id);
      setStatus('Device revoked.');
      onRefresh();
    } catch (e) {
      setStatus(e instanceof Error ? e.message : 'Revoke failed.');
    }
  }

  async function checkQueue() {
    setStatus(`${await queueLength()} point(s) waiting to sync.`);
  }

  return (
    <View style={styles.root}>
      <Text style={styles.title}>Account</Text>
      <Text>{email || 'Paired device (no email sign-in)'}</Text>
      <Text style={styles.muted}>Plan: {plan}</Text>
      <Text style={styles.muted}>
        {queued} point{queued === 1 ? '' : 's'} waiting to sync.
      </Text>
      <Text style={styles.title}>This device</Text>
      <Text style={styles.muted}>{deviceId ?? 'not paired yet'}</Text>
      <Text style={styles.title}>Other devices</Text>
      <FlatList
        data={devices.filter((d) => d.id !== deviceId)}
        keyExtractor={(d) => d.id}
        renderItem={({ item }) => (
          <View style={styles.row}>
            <Text style={styles.grow}>{item.name}</Text>
            <Button title="Revoke" onPress={() => revoke(item.id)} />
          </View>
        )}
        ListEmptyComponent={<Text style={styles.muted}>No other devices.</Text>}
      />
      <Text style={styles.title}>Sync server</Text>
      <TextInput
        style={styles.input}
        value={url}
        onChangeText={setUrl}
        placeholder="https://…/v1"
        autoCapitalize="none"
      />
      <Button title="Save endpoint" onPress={() => onApiUrl(url.trim())} />
      <View style={styles.row}>
        <Button title="Sync now" onPress={onRefresh} />
        <Button title="Queue?" onPress={checkQueue} />
      </View>
      {status ? <Text style={styles.muted}>{status}</Text> : null}
      <Button title="Sign out" color="#c23b3b" onPress={onSignOut} />
    </View>
  );
}

const styles = StyleSheet.create({
  root: { flex: 1, padding: 16, gap: 8 },
  title: { fontSize: 15, fontWeight: '700', marginTop: 10 },
  muted: { opacity: 0.65, fontSize: 13 },
  input: { borderWidth: 1, borderColor: '#ccc', borderRadius: 10, padding: 12, fontSize: 15 },
  row: { flexDirection: 'row', gap: 8, alignItems: 'center' },
  grow: { flex: 1 },
});

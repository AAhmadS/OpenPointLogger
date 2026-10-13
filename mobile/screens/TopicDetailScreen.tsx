// M4 Topic detail: entries grouped by sub-topic, edit text, delete. Built
// from pulled ops (plus anything still queued), so it reads the same offline
// and online.

import React, { useState } from 'react';
import { Button, FlatList, StyleSheet, Text, TextInput, TouchableOpacity, View } from 'react-native';
import type { EntryPayload, StoredOp } from '../src/types';
import { enqueue, newOpId, nextSeq } from '../src/queue';

interface Props {
  topicId: string;
  title: string;
  ops: StoredOp[];
  deviceId: string;
  onBack: () => void;
  onChanged: () => void;
}

interface Entry {
  id: string;
  subtopic: string;
  text: string;
  kind: string;
}

function entriesForTopic(topicId: string, ops: StoredOp[]): Entry[] {
  const byId = new Map<string, Entry>();
  for (const op of ops) {
    if (op.entity !== 'entry') continue;
    const p = op.payload as Partial<EntryPayload>;
    if (p.topic_id !== topicId) continue;
    if (op.op === 'delete') {
      byId.delete(op.entity_id);
      continue;
    }
    byId.set(op.entity_id, {
      id: op.entity_id,
      subtopic: p.subtopic ?? '',
      text: p.text ?? '',
      kind: p.kind ?? 'claim',
    });
  }
  return [...byId.values()];
}

export default function TopicDetailScreen({ topicId, title, ops, deviceId, onBack, onChanged }: Props) {
  const [editing, setEditing] = useState<string | null>(null);
  const [draft, setDraft] = useState('');
  const entries = entriesForTopic(topicId, ops);
  const groups = new Map<string, Entry[]>();
  for (const e of entries) {
    const key = e.subtopic || 'General';
    const arr = groups.get(key) ?? [];
    arr.push(e);
    groups.set(key, arr);
  }

  async function saveEdit(id: string) {
    const entry = entries.find((e) => e.id === id);
    if (!entry || !draft.trim()) return;
    await enqueue({
      op_id: newOpId(),
      device_id: deviceId,
      seq: await nextSeq(),
      entity: 'entry',
      entity_id: id,
      op: 'upsert',
      payload: { topic_id: topicId, subtopic: entry.subtopic, text: draft.trim(), kind: entry.kind },
      client_at: new Date().toISOString(),
    });
    setEditing(null);
    onChanged();
  }

  async function remove(id: string) {
    await enqueue({
      op_id: newOpId(),
      device_id: deviceId,
      seq: await nextSeq(),
      entity: 'entry',
      entity_id: id,
      op: 'delete',
      payload: { topic_id: topicId },
      client_at: new Date().toISOString(),
    });
    onChanged();
  }

  return (
    <View style={styles.root}>
      <Button title="‹ Topics" onPress={onBack} />
      <Text style={styles.title}>{title}</Text>
      <FlatList
        data={[...groups.entries()]}
        keyExtractor={([name]) => name}
        renderItem={({ item: [name, items] }) => (
          <View style={styles.group}>
            <Text style={styles.groupTitle}>{name}</Text>
            {items.map((e) =>
              editing === e.id ? (
                <View key={e.id} style={styles.card}>
                  <TextInput
                    style={styles.input}
                    value={draft}
                    onChangeText={setDraft}
                    multiline
                    autoFocus
                  />
                  <View style={styles.row}>
                    <Button title="Save" onPress={() => saveEdit(e.id)} />
                    <Button title="Cancel" onPress={() => setEditing(null)} />
                  </View>
                </View>
              ) : (
                <View key={e.id} style={styles.card}>
                  <Text>{e.text}</Text>
                  <View style={styles.row}>
                    <TouchableOpacity
                      onPress={() => {
                        setEditing(e.id);
                        setDraft(e.text);
                      }}>
                      <Text style={styles.link}>Edit</Text>
                    </TouchableOpacity>
                    <TouchableOpacity onPress={() => remove(e.id)}>
                      <Text style={[styles.link, styles.danger]}>Delete</Text>
                    </TouchableOpacity>
                  </View>
                </View>
              ),
            )}
          </View>
        )}
        ListEmptyComponent={<Text style={styles.empty}>No points yet.</Text>}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  root: { flex: 1, padding: 16, gap: 8 },
  title: { fontSize: 20, fontWeight: '700' },
  group: { marginTop: 12 },
  groupTitle: { fontSize: 13, fontWeight: '700', textTransform: 'uppercase', opacity: 0.6 },
  card: { padding: 12, borderWidth: 1, borderColor: '#e2e4e8', borderRadius: 12, marginTop: 6, gap: 8 },
  input: { borderWidth: 1, borderColor: '#ccc', borderRadius: 10, padding: 10, fontSize: 15 },
  row: { flexDirection: 'row', gap: 16 },
  link: { color: '#a15716', fontWeight: '600' },
  danger: { color: '#c23b3b' },
  empty: { opacity: 0.6, textAlign: 'center', marginTop: 24 },
});

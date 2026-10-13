// M3 Topics: open / closed list, plus starting a new topic (an op like any
// other - it queues offline and syncs later).

import React, { useState } from 'react';
import { Button, FlatList, StyleSheet, Text, TextInput, TouchableOpacity, View } from 'react-native';
import type { TopicSummary } from '../src/types';
import { enqueue, newOpId, nextSeq } from '../src/queue';

interface Props {
  topics: TopicSummary[];
  onOpen: (id: string) => void;
  deviceId: string;
  onChanged: () => void;
}

export default function TopicsScreen({ topics, onOpen, deviceId, onChanged }: Props) {
  const [title, setTitle] = useState('');
  const [filter, setFilter] = useState<'open' | 'closed'>('open');

  async function startTopic() {
    const name = title.trim();
    if (!name) return;
    await enqueue({
      op_id: newOpId(),
      device_id: deviceId,
      seq: await nextSeq(),
      entity: 'topic',
      entity_id: newOpId(),
      op: 'upsert',
      payload: { title: name, status: 'open' },
      client_at: new Date().toISOString(),
    });
    setTitle('');
    onChanged();
  }

  const shown = topics.filter((t) => t.status === filter);

  return (
    <View style={styles.root}>
      <View style={styles.row}>
        <TextInput
          style={[styles.input, styles.grow]}
          value={title}
          onChangeText={setTitle}
          placeholder="New topic name…"
        />
        <Button title="Start" onPress={startTopic} />
      </View>
      <View style={styles.row}>
        {(['open', 'closed'] as const).map((s) => (
          <TouchableOpacity
            key={s}
            style={[styles.chip, filter === s && styles.chipOn]}
            onPress={() => setFilter(s)}>
            <Text style={styles.cap}>{s}</Text>
          </TouchableOpacity>
        ))}
      </View>
      <FlatList
        data={shown}
        keyExtractor={(t) => t.topic_id}
        renderItem={({ item }) => (
          <TouchableOpacity style={styles.card} onPress={() => onOpen(item.topic_id)}>
            <Text style={styles.cardTitle}>{item.title}</Text>
            <Text style={styles.cardSub}>
              {item.points} point{item.points === 1 ? '' : 's'}
              {item.last_at ? ` · ${item.last_at.slice(0, 10)}` : ''}
            </Text>
          </TouchableOpacity>
        )}
        ListEmptyComponent={<Text style={styles.empty}>No {filter} topics yet.</Text>}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  root: { flex: 1, padding: 16, gap: 10 },
  row: { flexDirection: 'row', gap: 8, alignItems: 'center' },
  grow: { flex: 1 },
  input: { borderWidth: 1, borderColor: '#ccc', borderRadius: 10, padding: 12, fontSize: 16 },
  chip: { paddingVertical: 6, paddingHorizontal: 14, borderWidth: 1, borderColor: '#ccc', borderRadius: 999 },
  chipOn: { borderColor: '#a15716', backgroundColor: 'rgba(161,87,22,.12)' },
  cap: { textTransform: 'capitalize' },
  card: { padding: 14, borderWidth: 1, borderColor: '#e2e4e8', borderRadius: 12, marginBottom: 8 },
  cardTitle: { fontSize: 16, fontWeight: '600' },
  cardSub: { fontSize: 12, opacity: 0.6, marginTop: 2 },
  empty: { opacity: 0.6, textAlign: 'center', marginTop: 24 },
});

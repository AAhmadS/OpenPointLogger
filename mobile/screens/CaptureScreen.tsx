// M2 Capture: text, link, photo; active topic + sub-topic chips; kind
// toggle only when scientific mode is on. Saves to the offline queue first,
// then attempts a sync - a point is never lost to a tunnel.

import React, { useState } from 'react';
import { Button, StyleSheet, Text, TextInput, TouchableOpacity, View } from 'react-native';
import * as ImagePicker from 'expo-image-picker';
import type { EntryKind, TopicSummary } from '../src/types';
import { enqueue, newOpId, nextSeq } from '../src/queue';

interface Props {
  topics: TopicSummary[];
  activeTopicId: string | null;
  onPickTopic: (id: string) => void;
  scienceOn: boolean;
  deviceId: string;
  prefillUrl?: string | null;
  prefillText?: string | null;
  onSaved: () => void;
}

const KINDS: EntryKind[] = ['claim', 'note', 'quote'];

export default function CaptureScreen({
  topics,
  activeTopicId,
  onPickTopic,
  scienceOn,
  deviceId,
  prefillUrl,
  prefillText,
  onSaved,
}: Props) {
  const [text, setText] = useState(prefillText ?? '');
  const [link, setLink] = useState(prefillUrl ?? '');
  const [subtopic, setSubtopic] = useState('');
  const [kind, setKind] = useState<EntryKind>('claim');
  const [photo, setPhoto] = useState<string | null>(null);
  const [status, setStatus] = useState('');

  async function pickPhoto() {
    const perm = await ImagePicker.requestMediaLibraryPermissionsAsync();
    if (!perm.granted) {
      setStatus('Photo permission denied.');
      return;
    }
    const res = await ImagePicker.launchImageLibraryAsync({ base64: true, quality: 0.7 });
    if (!res.canceled && res.assets[0]?.base64) {
      setPhoto(`data:image/jpeg;base64,${res.assets[0].base64}`);
      setStatus('Photo attached.');
    }
  }

  async function save() {
    if (!activeTopicId) {
      setStatus('Pick a topic first.');
      return;
    }
    if (!text.trim()) {
      setStatus('Write the point first.');
      return;
    }
    const now = new Date().toISOString();
    const entryId = newOpId();
    await enqueue({
      op_id: newOpId(),
      device_id: deviceId,
      seq: await nextSeq(),
      entity: 'entry',
      entity_id: entryId,
      op: 'upsert',
      payload: { topic_id: activeTopicId, subtopic: subtopic.trim(), text: text.trim(), kind },
      client_at: now,
    });
    if (link.trim()) {
      await enqueue({
        op_id: newOpId(),
        device_id: deviceId,
        seq: await nextSeq(),
        entity: 'source',
        entity_id: newOpId(),
        op: 'upsert',
        payload: { entry_id: entryId, type: 'link', value: link.trim() },
        client_at: now,
      });
    }
    if (photo) {
      await enqueue({
        op_id: newOpId(),
        device_id: deviceId,
        seq: await nextSeq(),
        entity: 'source',
        entity_id: newOpId(),
        op: 'upsert',
        payload: { entry_id: entryId, type: 'image', value: photo },
        client_at: now,
      });
    }
    setText('');
    setLink('');
    setPhoto(null);
    setStatus('Saved - syncs when online.');
    onSaved();
  }

  return (
    <View style={styles.root}>
      <Text style={styles.label}>Topic</Text>
      <View style={styles.chips}>
        {topics.filter((t) => t.status === 'open').map((t) => (
          <TouchableOpacity
            key={t.topic_id}
            style={[styles.chip, t.topic_id === activeTopicId && styles.chipOn]}
            onPress={() => onPickTopic(t.topic_id)}>
            <Text>{t.title}</Text>
          </TouchableOpacity>
        ))}
      </View>
      {scienceOn && (
        <View style={styles.chips}>
          {KINDS.map((k) => (
            <TouchableOpacity
              key={k}
              style={[styles.chip, k === kind && styles.chipOn]}
              onPress={() => setKind(k)}>
              <Text>{k}</Text>
            </TouchableOpacity>
          ))}
        </View>
      )}
      <TextInput
        style={[styles.input, styles.multiline]}
        value={text}
        onChangeText={setText}
        placeholder="The point…"
        multiline
      />
      <TextInput
        style={styles.input}
        value={subtopic}
        onChangeText={setSubtopic}
        placeholder="Sub-topic (optional)"
      />
      <TextInput
        style={styles.input}
        value={link}
        onChangeText={setLink}
        placeholder="Source link (optional)"
        autoCapitalize="none"
      />
      <View style={styles.row}>
        <Button title={photo ? 'Photo attached ✓' : '+ Photo'} onPress={pickPhoto} />
        <Button title="Log point" onPress={save} />
      </View>
      {status ? <Text style={styles.status}>{status}</Text> : null}
    </View>
  );
}

const styles = StyleSheet.create({
  root: { flex: 1, padding: 16, gap: 10 },
  label: { fontSize: 12, fontWeight: '600', textTransform: 'uppercase' },
  chips: { flexDirection: 'row', flexWrap: 'wrap', gap: 6 },
  chip: { paddingVertical: 6, paddingHorizontal: 12, borderWidth: 1, borderColor: '#ccc', borderRadius: 999 },
  chipOn: { borderColor: '#a15716', backgroundColor: 'rgba(161,87,22,.12)' },
  input: { borderWidth: 1, borderColor: '#ccc', borderRadius: 10, padding: 12, fontSize: 16 },
  multiline: { minHeight: 90, textAlignVertical: 'top' },
  row: { flexDirection: 'row', justifyContent: 'space-between' },
  status: { fontSize: 13, opacity: 0.7 },
});

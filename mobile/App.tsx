// Trailmark Capture (Android V1, M1-M6). Tab shell without a router
// dependency: signed out -> PairScreen, signed in -> Capture / Topics /
// Settings. Share intents (M6) prefill Capture. Before the backend exists
// everything runs against MockTransport; flipping to HttpTransport is one
// constructor plus the API URL in Settings.

import React, { useCallback, useEffect, useState } from 'react';
import { Button, SafeAreaView, StyleSheet, Text, TouchableOpacity, View } from 'react-native';
import { StatusBar } from 'expo-status-bar';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { TrailmarkApi } from './src/api';
import { HttpTransport, MockTransport, type SyncTransport } from './src/transport';
import { syncNow } from './src/sync';
import { peekQueue, queueLength } from './src/queue';
import type { StoredOp, TopicSummary } from './src/types';
import { readShareIntent } from './src/share';
import { CrashBoundary, CrashScreen, clearFatal, installGlobalHandler, loadFatal } from './src/crashlog';
import PairScreen from './screens/PairScreen';
import CaptureScreen from './screens/CaptureScreen';
import TopicsScreen from './screens/TopicsScreen';
import TopicDetailScreen from './screens/TopicDetailScreen';
import SettingsScreen from './screens/SettingsScreen';

const TOKEN_KEY = 'trailmark.session.token';
const EMAIL_KEY = 'trailmark.session.email';
const DEVICE_KEY = 'trailmark.session.device';
const URL_KEY = 'trailmark.api.url';
const CURSOR_KEY = 'trailmark.sync.cursor';
const DEFAULT_URL = 'https://api.trailmark.chantex.ir/v1';

// Registered once at module load: persists any fatal JS error so the next
// launch can show it instead of dying silently again.
installGlobalHandler();

type Tab = 'capture' | 'topics' | 'settings';

export default function App() {
  const [apiUrl, setApiUrl] = useState(DEFAULT_URL);
  const [api, setApi] = useState<TrailmarkApi | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [email, setEmail] = useState('');
  const [deviceId, setDeviceId] = useState('local-device');
  const [transport, setTransport] = useState<SyncTransport>(() => new MockTransport());
  const [tab, setTab] = useState<Tab>('capture');
  const [topics, setTopics] = useState<TopicSummary[]>([]);
  const [ops, setOps] = useState<StoredOp[]>([]);
  const [activeTopicId, setActiveTopicId] = useState<string | null>(null);
  const [detailId, setDetailId] = useState<string | null>(null);
  const [queued, setQueued] = useState(0);
  const [scienceOn] = useState(false);
  const [prefill, setPrefill] = useState<{ text?: string; url?: string } | null>(null);
  const [booted, setBooted] = useState(false);
  const [fatal, setFatal] = useState<{ message: string; at: string } | null>(null);

  const getToken = useCallback(async () => token, [token]);

  useEffect(() => {
    (async () => {
      const [t, e, d, u] = await Promise.all([
        AsyncStorage.getItem(TOKEN_KEY),
        AsyncStorage.getItem(EMAIL_KEY),
        AsyncStorage.getItem(DEVICE_KEY),
        AsyncStorage.getItem(URL_KEY),
      ]);
      const url = u || DEFAULT_URL;
      setApiUrl(url);
      const client = new TrailmarkApi(url, getToken);
      setApi(client);
      if (t) {
        setToken(t);
        setEmail(e ?? '');
        setDeviceId(d ?? 'local-device');
        // Backend reachable? Use it; otherwise stay on the mock until the
        // user saves a working endpoint. A failed pull here is routine
        // (offline, backend not deployed yet) - never a boot error.
        try {
          const page = await new HttpTransport(client).pull(undefined, 1);
          void page;
          setTransport(new HttpTransport(client));
        } catch {
          setTransport(new MockTransport());
        }
      }
      setPrefill(await readShareIntent());
      setFatal(await loadFatal());
      setBooted(true);
    })();
  }, [getToken]);

  const refresh = useCallback(async () => {
    try {
      const cursor = await AsyncStorage.getItem(CURSOR_KEY);
      const report = await syncNow(transport, cursor);
      if (report.cursor) await AsyncStorage.setItem(CURSOR_KEY, report.cursor);
      setTopics(report.topics);
      const pulled = await transport.pull(undefined, 500);
      setOps(pulled.ops.concat(await peekQueue().then((q) =>
        q.map(
          (o): StoredOp => ({ ...o, applied_at: new Date().toISOString() }),
        ),
      )));
      setQueued(await queueLength());
      if (!activeTopicId) {
        const open = report.topics.find((t) => t.status === 'open');
        if (open) setActiveTopicId(open.topic_id);
      }
    } catch {
      // Offline or backend not up: show what the queue and the mock know.
      setTopics(await transport.topics());
      setQueued(await queueLength());
    }
  }, [transport, activeTopicId]);

  useEffect(() => {
    if (booted && token) void refresh();
  }, [booted, token, refresh]);

  async function signOut() {
    await Promise.all([
      AsyncStorage.removeItem(TOKEN_KEY),
      AsyncStorage.removeItem(EMAIL_KEY),
      AsyncStorage.removeItem(DEVICE_KEY),
    ]);
    setToken(null);
    setTransport(new MockTransport());
    setTab('capture');
  }

  if (!booted || !api) {
    return (
      <SafeAreaView style={styles.root}>
        <Text>Loading…</Text>
      </SafeAreaView>
    );
  }

  if (fatal) {
    return (
      <SafeAreaView style={styles.root}>
        <StatusBar style="auto" />
        <CrashScreen
          message={`Last launch died at ${fatal.at}:\n${fatal.message}`}
          onDismiss={() => {
            void clearFatal().then(() => setFatal(null));
          }}
        />
      </SafeAreaView>
    );
  }

  if (!token) {
    return (
      <SafeAreaView style={styles.root}>
        <StatusBar style="auto" />
        <CrashBoundary>
        <PairScreen
          api={api}
          onPaired={async (s) => {
            await Promise.all([
              AsyncStorage.setItem(TOKEN_KEY, s.accessToken),
              AsyncStorage.setItem(EMAIL_KEY, s.email),
              AsyncStorage.setItem(DEVICE_KEY, s.deviceId ?? 'local-device'),
            ]);
            setToken(s.accessToken);
            setEmail(s.email);
            setDeviceId(s.deviceId ?? 'local-device');
            setTransport(new MockTransport());
          }}
        />
        </CrashBoundary>
      </SafeAreaView>
    );
  }

  const detailTopic = detailId ? topics.find((t) => t.topic_id === detailId) : undefined;

  return (
    <SafeAreaView style={styles.root}>
      <StatusBar style="auto" />
      <CrashBoundary>
      <View style={styles.body}>
        {detailTopic ? (
          <TopicDetailScreen
            topicId={detailTopic.topic_id}
            title={detailTopic.title}
            ops={ops}
            deviceId={deviceId}
            onBack={() => setDetailId(null)}
            onChanged={() => void refresh()}
          />
        ) : tab === 'capture' ? (
          <CaptureScreen
            topics={topics}
            activeTopicId={activeTopicId}
            onPickTopic={setActiveTopicId}
            scienceOn={scienceOn}
            deviceId={deviceId}
            prefillUrl={prefill?.url ?? null}
            prefillText={prefill?.text ?? null}
            onSaved={() => void refresh()}
          />
        ) : tab === 'topics' ? (
          <TopicsScreen
            topics={topics}
            onOpen={(id) => setDetailId(id)}
            deviceId={deviceId}
            onChanged={() => void refresh()}
          />
        ) : (
          <SettingsScreen
            email={email}
            plan="free"
            deviceId={deviceId}
            devices={[]}
            transport={transport}
            apiUrl={apiUrl}
            onApiUrl={async (u) => {
              setApiUrl(u);
              await AsyncStorage.setItem(URL_KEY, u);
              const client = new TrailmarkApi(u, getToken);
              setApi(client);
              setTransport(new HttpTransport(client));
              void refresh();
            }}
            queued={queued}
            onRefresh={() => void refresh()}
            onSignOut={() => void signOut()}
          />
        )}
      </View>
      {!detailTopic && (
        <View style={styles.tabs}>
          {(['capture', 'topics', 'settings'] as const).map((t) => (
            <TouchableOpacity
              key={t}
              style={[styles.tab, tab === t && styles.tabOn]}
              onPress={() => {
                setTab(t);
                void refresh();
              }}>
              <Text style={styles.cap}>{t}</Text>
            </TouchableOpacity>
          ))}
          <Button title="Sync" onPress={() => void refresh()} />
        </View>
      )}
      </CrashBoundary>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  root: { flex: 1 },
  body: { flex: 1 },
  tabs: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    padding: 8,
    borderTopWidth: 1,
    borderTopColor: '#e2e4e8',
  },
  tab: { flex: 1, padding: 10, alignItems: 'center', borderRadius: 10 },
  tabOn: { backgroundColor: 'rgba(161,87,22,.12)' },
  cap: { textTransform: 'capitalize', fontWeight: '600' },
});

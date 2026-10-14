// Crash visibility: in release builds an uncaught JS error kills the app
// with no message. This boundary renders the error on screen instead, and
// the global handler persists launch-time fatals so the NEXT launch shows
// what died. If the app still vanishes with no screen at all, the crash is
// native (below JS) and needs a device log (adb logcat), not this file.

import React from 'react';
import { Button, ScrollView, StyleSheet, Text, View } from 'react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';

const CRASH_KEY = 'trailmark.lastfatal.v1';

export async function saveFatal(message: string): Promise<void> {
  try {
    await AsyncStorage.setItem(
      CRASH_KEY,
      JSON.stringify({ message: message.slice(0, 2000), at: new Date().toISOString() }),
    );
  } catch {
    // Storage itself broken: nothing to persist to.
  }
}

export async function loadFatal(): Promise<{ message: string; at: string } | null> {
  try {
    const raw = await AsyncStorage.getItem(CRASH_KEY);
    return raw ? (JSON.parse(raw) as { message: string; at: string }) : null;
  } catch {
    return null;
  }
}

export async function clearFatal(): Promise<void> {
  try {
    await AsyncStorage.removeItem(CRASH_KEY);
  } catch {
    // Best effort.
  }
}

let handlerInstalled = false;

export function installGlobalHandler(): void {
  if (handlerInstalled) return;
  handlerInstalled = true;
  const E = (global as unknown as { ErrorUtils?: { setGlobalHandler(fn: (e: unknown) => void): void } })
    .ErrorUtils;
  E?.setGlobalHandler((e: unknown) => {
    const message = e instanceof Error ? `${e.name}: ${e.message}\n${e.stack ?? ''}` : String(e);
    void saveFatal(message);
  });
}

interface BoundaryState {
  error: string | null;
}

export class CrashBoundary extends React.Component<{ children: React.ReactNode }, BoundaryState> {
  state: BoundaryState = { error: null };

  static getDerivedStateFromError(error: unknown): BoundaryState {
    const message =
      error instanceof Error ? `${error.name}: ${error.message}\n${error.stack ?? ''}` : String(error);
    void saveFatal(message);
    return { error: message };
  }

  render(): React.ReactNode {
    if (this.state.error) {
      return <CrashScreen message={this.state.error} onDismiss={() => this.setState({ error: null })} />;
    }
    return this.props.children;
  }
}

export function CrashScreen({ message, onDismiss }: { message: string; onDismiss: () => void }): React.JSX.Element {
  return (
    <View style={styles.root}>
      <Text style={styles.title}>Something broke</Text>
      <Text style={styles.sub}>
        The app hit an error instead of your screen. Send this text with your report:
      </Text>
      <ScrollView style={styles.box}>
        <Text style={styles.mono} selectable>
          {message}
        </Text>
      </ScrollView>
      <Button title="Dismiss" onPress={onDismiss} />
    </View>
  );
}

const styles = StyleSheet.create({
  root: { flex: 1, padding: 24, gap: 12, justifyContent: 'center' },
  title: { fontSize: 24, fontWeight: '700' },
  sub: { fontSize: 14, opacity: 0.7 },
  box: { maxHeight: 300, borderWidth: 1, borderColor: '#ccc', borderRadius: 10, padding: 12 },
  mono: { fontFamily: 'monospace', fontSize: 12 },
});

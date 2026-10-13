// M1 sign-in / pair. Two routes, same destination: email OTP (magic link
// style), or the 6-char pairing code shown on the desktop.

import React, { useState } from 'react';
import { Button, StyleSheet, Text, TextInput, View } from 'react-native';
import { TrailmarkApi } from '../src/api';

interface Props {
  api: TrailmarkApi;
  onPaired: (session: {
    accessToken: string;
    email: string;
    deviceId: string | null;
  }) => void;
}

export default function PairScreen({ api, onPaired }: Props) {
  const [email, setEmail] = useState('');
  const [otpSent, setOtpSent] = useState(false);
  const [otp, setOtp] = useState('');
  const [code, setCode] = useState('');
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);

  async function sendOtp() {
    setError('');
    setBusy(true);
    try {
      await api.otpRequest(email.trim());
      setOtpSent(true);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Could not send the code.');
    } finally {
      setBusy(false);
    }
  }

  async function verifyOtp() {
    setError('');
    setBusy(true);
    try {
      const r = await api.otpVerify(email.trim(), otp.trim());
      onPaired({ accessToken: r.access_token, email: r.user.email, deviceId: null });
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Sign-in failed.');
    } finally {
      setBusy(false);
    }
  }

  async function pairWithCode() {
    setError('');
    setBusy(true);
    try {
      const r = await api.pair(code.trim(), 'Android phone');
      // Pairing implies the account behind the code; the access token for
      // day-to-day calls still comes from OTP - this keeps one token shape.
      onPaired({ accessToken: r.device_token, email: '', deviceId: r.device_id });
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Pairing failed.');
    } finally {
      setBusy(false);
    }
  }

  return (
    <View style={styles.root}>
      <Text style={styles.title}>Trailmark</Text>
      <Text style={styles.sub}>Log the point. Keep the source.</Text>
      <Text style={styles.label}>Email sign-in</Text>
      <TextInput
        style={styles.input}
        value={email}
        onChangeText={setEmail}
        placeholder="you@example.com"
        keyboardType="email-address"
        autoCapitalize="none"
      />
      {!otpSent ? (
        <Button title={busy ? 'Sending…' : 'Send code'} onPress={sendOtp} disabled={busy} />
      ) : (
        <>
          <TextInput
            style={styles.input}
            value={otp}
            onChangeText={setOtp}
            placeholder="6-digit code"
            keyboardType="number-pad"
            maxLength={6}
          />
          <Button title={busy ? 'Checking…' : 'Sign in'} onPress={verifyOtp} disabled={busy} />
        </>
      )}
      <Text style={styles.label}>Or pair with the desktop</Text>
      <TextInput
        style={styles.input}
        value={code}
        onChangeText={setCode}
        placeholder="6-char code from the desktop"
        autoCapitalize="characters"
        maxLength={6}
      />
      <Button title={busy ? 'Pairing…' : 'Pair'} onPress={pairWithCode} disabled={busy} />
      {error ? <Text style={styles.error}>{error}</Text> : null}
    </View>
  );
}

const styles = StyleSheet.create({
  root: { flex: 1, padding: 24, gap: 10, justifyContent: 'center' },
  title: { fontSize: 28, fontWeight: '700' },
  sub: { fontSize: 14, opacity: 0.6, marginBottom: 12 },
  label: { fontSize: 12, fontWeight: '600', marginTop: 8, textTransform: 'uppercase' },
  input: { borderWidth: 1, borderColor: '#ccc', borderRadius: 10, padding: 12, fontSize: 16 },
  error: { color: '#c23b3b', marginTop: 8 },
});

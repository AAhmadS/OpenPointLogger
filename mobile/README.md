# Trailmark Capture — Android V1 (T21)

React Native + Expo, sideloaded APK (no Play account, per owner decision
2026-09-22). Screens M1–M6 per `../.claude/PRODUCT_SPEC.md` §4.3; wire
protocol is `../api/openapi.yaml`, storage is `../api/schema.dbml`.
Export stays desktop-only in V1 (spec D-8).

## Status

Scaffold + contract, running against `MockTransport` (in-memory). The two
owner gates before anything syncs for real:

1. **Supabase project** — project URL + anon key, region still not
   established. Then implement the contract (auth passthrough, devices,
   op-log, signed uploads) and point `extra.apiBaseUrl` / Settings at it.
2. **Expo account + `eas login`** — then `npm run build:apk` produces the
   installable APK from the cloud (`preview` profile, `buildType: apk`).

Next code steps after the gates: desktop pairing-code surface + desktop
op-log applier into `points.json` (no desktop HTTP server exists yet), then
flip `App.tsx` to `HttpTransport` once the backend answers.

## Develop

```sh
cd mobile
npm install          # done once; pinned in package-lock.json
npx expo start       # scan with Expo Go, or press a for a local emulator
npm run typecheck
```

## Ship the APK (one interactive login, then cloud build)

```sh
cd mobile
eas login            # Expo account, browser SSO - interactive, once per machine
eas build --platform android --profile preview
```

The first build links `extra.eas.projectId` (currently a placeholder) and
creates the Android keystore on EAS (kept server-side; back it up from the
Expo dashboard). It uploads the APK to an EAS build page and prints a
download URL — attach that APK to the matching GitHub seed release next to
the Windows exe. `tsc`, `expo prebuild` and the manifest (package
`ir.chantex.trailmark`, share-target intents, photo permission) are already
verified; nothing else stands between this tree and the APK but the login.

Share-sheet target (M6) is declared in `app.json` intent filters;
`src/share.ts` reads the launch intent into Capture. Photo attach uses
`expo-image-picker` (base64, 8 MB server cap enforced in the contract).

## Files

- `App.tsx` — tab shell (Capture / Topics / Settings), session + sync state
- `screens/` — M1 Pair, M2 Capture, M3 Topics, M4 TopicDetail, M5 Settings
- `src/api.ts` — typed fetch client for the contract, no dependencies
- `src/transport.ts` — `SyncTransport` + `HttpTransport` + `MockTransport`
- `src/queue.ts` — offline op queue (AsyncStorage, survives process death)
- `src/sync.ts` — push-drain then pull; idempotent by `op_id` both ends
- `src/share.ts` — M6 intent prefill

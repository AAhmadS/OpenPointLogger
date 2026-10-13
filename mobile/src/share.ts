// M6 share-sheet target. Android delivers shared text/images to the launch
// intent; expo-linking surfaces the initial URL. Returns prefill for the
// Capture screen, or null when the app was opened normally.

import * as Linking from 'expo-linking';

export interface SharePrefill {
  text?: string;
  url?: string;
}

export async function readShareIntent(): Promise<SharePrefill | null> {
  try {
    const url = await Linking.getInitialURL();
    if (!url) return null;
    // Plain text shares arrive as the URL itself or in a query param.
    if (/^https?:\/\//i.test(url)) return { url };
    const parsed = Linking.parse(url);
    const qp = parsed.queryParams ?? {};
    const text =
      typeof qp.text === 'string'
        ? qp.text
        : typeof qp.url === 'string'
          ? qp.url
          : undefined;
    if (!text) return null;
    return /^https?:\/\//i.test(text) ? { url: text } : { text };
  } catch {
    return null;
  }
}

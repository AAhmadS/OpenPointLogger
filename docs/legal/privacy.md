> **DRAFT — NOT IN FORCE.** Written 2026-09-22. No lawyer has reviewed this.
> Placeholders marked `[TO SUPPLY: ...]` are deliberately unfilled. See
> `docs/legal/README.md` before publishing.

# Privacy Policy — Trailmark

**Controller:** Chantex ([TO SUPPLY: full legal form and registered address])
**Service:** Trailmark, the desktop application and the website at
`trailmark.chantex.ir`
**Version:** draft of 2026-09-22 · **Effective:** [TO SUPPLY: publication date]

---

## 1. The short version

Trailmark is a local-first application. Everything you write stays on your own
computer unless you deliberately turn on a feature that sends it somewhere, and
each of those features uses a key or token that belongs to you, not to us.

**There is no telemetry, no analytics and no usage tracking in the desktop
application.** That is a statement about the code, and it is checkable: the
only four modules in the application that open a network connection are the AI
client, the transcription client, the citation lookup, and the Telegram bridge.
None of them reports to us, and none of them runs until you enable it.

Today, in the shipped desktop application, **we hold no data about you at
all** — because there are no accounts and no server.

## 2. What is stored on your own computer

Under your Windows user profile, at `%APPDATA%\Trailmark`:

| File or folder | Contents |
|---|---|
| `points.json` | Your topics, subtopics, points and their sources — the substance of your work. |
| `config.json` | Your settings, including any API keys and the Telegram bot token you enter. |
| `attachments/` | Images and screenshots you attach to points. |
| `exports/` | Reports generated from closed topics. |

We never see any of it. It is deleted when you delete it, and it survives
uninstalling the application unless you remove the folder yourself.

**One thing to know about `config.json`:** the API keys and bot token you enter
are stored there in plain text, protected by your operating system's file
permissions and nothing else. Anyone with access to your user profile — or to
an unencrypted backup of it — can read them. Treat that folder the way you
would treat a file of passwords, and prefer a key scoped to Trailmark alone so
it can be revoked without disturbing anything else.

## 3. What we collect

**Desktop application:** nothing. No account, no identifier, no crash reports,
no usage statistics, no update pings.

**Website (`trailmark.chantex.ir`):** [TO SUPPLY: the website does not exist
yet. When it does, state exactly what its hosting produces — server access logs
and their retention, any analytics, any cookies — and do not claim less than is
true. If analytics are added, they belong here, and §1 must be corrected.]

**Accounts and sync (planned, not built):** when accounts exist we will hold
your email address, authentication credentials in hashed form, and — if you
enable sync — a copy of your topics, points and attached screenshots. Exports
are not synced. Nothing in this paragraph is collected today.

## 4. Data you send to third parties by enabling a feature

Each feature below is off by default and requires you to enter your own
credential. When you use one, the data goes from your computer directly to that
provider. It does not pass through us, and we keep no copy.

| Feature | Recipient | What is sent |
|---|---|---|
| AI assist | The provider you select — OpenRouter (default), OpenAI, Mistral, AvalAI, or Google AI Studio | The text of the points being polished or summarised |
| Voice logging | The transcription endpoint you configure (OpenRouter by default) | Audio recorded from your microphone, and its transcript in return |
| Telegram bridge | Telegram | Messages and files exchanged with your bot, via Telegram's servers |
| Citation lookup | `doi.org` and Crossref | The DOI or identifier you entered |

Because the key is yours, **that provider's privacy policy governs what happens
to your data there** — including whether they retain it, how long for, and
whether they use it for training. Read the policy of whichever provider you
choose. We have no visibility into those requests and cannot delete anything
from them on your behalf.

Voice logging deserves a specific warning: when it is on, the microphone is
being listened to and speech is being sent to a third party for transcription.
Anyone else in the room is being recorded too, and they have not agreed to
this. Turn it off when you are not using it.

## 5. Why we process data, and on what basis

Today there is nothing to state here, because the desktop application processes
no personal data on our behalf.

When accounts exist:

| Purpose | Data | Lawful basis |
|---|---|---|
| Creating and securing your account | Email, hashed credentials | Performance of a contract |
| Synchronising your content between your devices | Topics, points, screenshots | Performance of a contract |
| Taking payment | [TO SUPPLY: whatever the chosen provider requires] | Performance of a contract |
| Keeping the service secure and preventing abuse | Access logs, IP address | Legitimate interests |
| Meeting legal and accounting obligations | Transaction records | Legal obligation |

We do not use your content to train AI models, and we do not profile you or
make automated decisions about you.

## 6. Who we share data with

We do not sell your data and we do not share it with advertisers.

When accounts and sync exist, one sub-processor will hold your synced content:
[TO SUPPLY: the managed backend provider — a managed BaaS was chosen on
2026-09-22 but the specific vendor and the hosting region were not decided.
Name both here before publishing; "a cloud provider" is not an answer a reader
can act on.]

A payment provider will be added to this list when paid plans launch
([TO SUPPLY]).

We may disclose data where we are legally required to. Where we are permitted
to tell you, we will.

## 7. International transfers

[TO SUPPLY: depends entirely on the hosting region, which is undecided. Once
the region is chosen, state where the data is held, and — if it leaves the
region users are in — the mechanism relied on for that transfer. Do not draft
this before the region exists; a transfer mechanism named for a region nobody
has picked is worse than an honest blank.]

## 8. How long we keep things

Local files on your computer: until you delete them. We have no control over
this and no ability to reach them.

Synced content, once sync exists: for as long as your account is open, and
deleted within [TO SUPPLY: retention period] of you closing it, except where
law requires us to keep a record for longer.

Access and security logs: [TO SUPPLY: retention period].

## 9. Your rights

Where data protection law gives you rights over personal data we hold — and
this includes the GDPR if you are in the EEA or UK — you may request access to
it, correction of it, deletion of it, a portable copy of it, restriction of its
processing, or object to processing based on legitimate interests. You may also
withdraw consent where we relied on it, and complain to your local supervisory
authority.

Two honest notes about these rights:

- **Today they mostly have nothing to operate on**, because we hold no data.
  For the desktop application, your access, portability and deletion rights are
  satisfied by the files in `%APPDATA%\Trailmark`: they are plain JSON, they
  are already yours, and deleting them is deletion.
- **We cannot exercise your rights against a third-party AI provider.** Data
  you sent to OpenRouter or Telegram under your own account is between you and
  them; ask them directly.

To make a request, write to [TO SUPPLY: privacy contact address]. We will
respond within one month.

## 10. Children

Trailmark is not directed at children and we do not knowingly collect data from
anyone under [TO SUPPLY: minimum age for the chosen jurisdiction]. If you
believe a child has given us personal data, contact us and we will delete it.

## 11. Security

The desktop application's security is your operating system's: files under your
user profile, protected by your account. We recommend full-disk encryption if
you record anything sensitive, and a Trailmark-specific API key that can be
revoked on its own.

For server-side features, when they exist: [TO SUPPLY: encryption in transit
and at rest, access controls, and the breach-notification commitment. Write
this against what the chosen provider actually gives you, not against what
sounds reassuring.]

If a breach affects your personal data and presents a risk to you, we will
notify you and the relevant authority as the law requires.

## 12. Changes to this policy

We will post any update at `trailmark.chantex.ir/privacy` with a new version
date. If a change materially affects how we handle your personal data we will
give notice in the application and by email, where we have one, before it takes
effect.

## 13. Contact

Chantex — [TO SUPPLY: privacy contact address]
`trailmark.chantex.ir`

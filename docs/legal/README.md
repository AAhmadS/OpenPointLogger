# Legal texts — drafts, not in force

Two documents live here: `terms.md` and `privacy.md`. Both were drafted on
2026-09-22 against what the code in this repository actually does, not against
a template. Neither is in force. Publishing them is the owner's signature, and
that is the human gate `legal-text-terms-privacy` in
`.claude/gates/platform-expansion.yaml`.

## How to finish them

Every place where a fact is genuinely unknown is marked `[TO SUPPLY: ...]`.
These are deliberately left empty rather than filled with a plausible guess —
a company address, a registration number or a jurisdiction invented to make a
document look complete is exactly the failure this project's evidence rules
exist to prevent. Fill each one, delete the brackets, then strike this README
and the "draft" banners at the top of both files.

There are **[TO SUPPLY]** markers for: the trading entity's full legal form and
address, the governing jurisdiction, a contact address for legal and privacy
notices, and the sync provider's identity and hosting region (undecided as of
this draft).

## What still has to change before they are true

Both documents describe the product as it exists **today**: a local-first
Windows desktop app with no account, plus optional integrations the user turns
on themselves. Three changes on the roadmap will make parts of them wrong:

- **Accounts and sync** (T18). The moment there is a server holding user
  content, the privacy policy needs the sub-processor named, the region stated,
  and a retention and deletion period fixed.
- **Billing** (T19). Terms §7 is written for a product that takes no money yet.
  When a payment provider is chosen it becomes a named sub-processor and the
  refund and cancellation terms have to be real.
- **Hosted AI keys** (T20). Today every AI call uses a key the *user* supplies,
  which is why the provider is the user's own counterparty. If Trailmark starts
  reselling access, Chantex becomes the controller for those calls and §4 of
  the privacy policy changes substantially.

Do not publish a version that promises any of these before they are built.

## Review before publishing

These are drafts written by an agent. No lawyer has reviewed them. That is a
statement of fact, not a disclaimer to be edited out — if a qualified review
happens, record who did it and when, here.

# Making your own Trailmark template

A Trailmark template is a folder with a manifest and one HTML file. Nothing is
compiled, nothing is installed, and nothing about it is Trailmark-specific
beyond a handful of `{{placeholders}}` — it is a normal HTML page with holes in
it. If you can write a web page you can write a template in about twenty
minutes.

Trailmark ships with three: **Research Roam**, **Personal Report** and
**Protocol**. They are deliberately generic starting points. The interesting
templates are the ones you write for your own work, and those live outside the
repo where they stay yours.

---

## 1. Where templates live

| | Path |
|---|---|
| **Yours** | `%APPDATA%\Trailmark\templates\<your-id>\` |
| Built-in | next to the app (`templates/` in the repo, bundled inside the `.exe`) |

Settings → Exports → **Open templates folder** opens the first one for you.

A folder in your templates directory whose `id` matches a built-in one
**replaces** the built-in. That is the supported way to fork a shipped template:
copy it across, keep the id, edit freely, and a Trailmark update will not
overwrite you.

Templates are discovered when the export dialog opens. There is no install step
and no restart — add the folder, open the dialog, it is there.

---

## 2. The folder

```
my-template/
  template.json     required — the manifest
  template.html     required — the page
  template.tex      optional — only if you want a real LaTeX build
  logo.svg          optional — any asset, referenced by relative path
```

Relative assets (`<img src="logo.svg">`, `<link href="extra.css">`) are read at
export time and inlined as `data:` URIs, so an exported HTML file is a single
portable document with no folder next to it. Assets must sit inside the template
folder; a path that climbs out with `../` is refused. The cap is 4 MB per asset.

### `template.json`

```json
{
  "id": "field-notes",
  "name": "Field Notes",
  "purpose": "personal",
  "description": "What this template is for, one or two sentences. Shown in the export dialog.",
  "kicker": "Field Notes",
  "accent": "#0f766e",
  "formats": ["html", "pdf", "markdown", "docx"],
  "page": { "size": "A4", "margin": "18mm 16mm 20mm" },
  "local_only": true
}
```

| Key | Meaning |
|---|---|
| `id` | Folder-safe identifier. Must match the folder name. Shadows a built-in of the same id. |
| `name` | What the export dialog shows. |
| `purpose` | Free text: `research`, `personal`, `procedure`, `business`, `team`… Used for grouping only. |
| `description` | The sentence under the name in the picker. Write it for the person choosing, not for you. |
| `kicker` | Default value of `{{kicker}}` — the small line above the title. |
| `accent` | One hex colour. Reaches the page as `{{accent}}` and LaTeX as `{{accent_hex}}` (no `#`). |
| `formats` | Which buttons are offered. `html`, `pdf`, `markdown`, `docx`, `latex`. |
| `page` | Passed through for your own use; the real page geometry is your `@page` rule. |
| `local_only` | `true` marks a template as yours. It never ships and is skipped by the repo. |

`markdown` and `docx` do not use `template.html` at all — they are generated
from the same composed Markdown, with `accent` applied to the DOCX heading
colour. Listing them costs you nothing.

---

## 3. Placeholders

Two forms:

- `{{name}}` — replaced by a value. Unknown names are replaced with nothing, so
  a typo silently empties a region rather than printing `{{typo}}`.
- `{{#name}} … {{/name}}` — a **conditional block**. The block is kept when
  `name` has a value and deleted entirely when it does not. Use it for anything
  optional so an empty author does not leave a dangling `by` on the cover.

Every value the pipeline guarantees:

| Placeholder | Contents |
|---|---|
| `{{title}}` | Report title, HTML-escaped |
| `{{subtitle}}` | Sub-title / topic descriptor |
| `{{kicker}}` | Small uppercase line above the title |
| `{{author}}` | Author from Settings — often empty |
| `{{org}}` | Organisation from Settings — often empty |
| `{{date}}` | Long-form generation date |
| `{{date_iso}}` | `YYYY-MM-DD` |
| `{{period}}` | The span the points were collected over |
| `{{body}}` | **The report itself, as HTML.** `<h2 id="s-…">`, `<p>`, `<ul>`, `<blockquote>`, `<code>`, `<a class="cite">` |
| `{{toc}}` | `<nav><ol>…` of the body's H2s. Empty under 3 sections — wrap it in `{{#toc}}…{{/toc}}` |
| `{{references}}` | `<li id="r1">…` items, already numbered, for you to put inside your own `<ol>` |
| `{{figures}}` | `<figure><img><figcaption>` blocks for attached screenshots |
| `{{summary}}` | One-paragraph abstract. Often empty |
| `{{count_points}}` | Number of logged points |
| `{{count_sources}}` | Number of distinct cited sources |
| `{{footer}}` | Footer line |
| `{{accent}}` | Accent colour with `#` |
| `{{accent_hex}}` | Accent colour without `#`, for LaTeX `\definecolor` |
| `{{app_version}}` | Trailmark version |

Citations in the body render as `<a class="cite" href="#r3">[3]</a>`, so giving
your `<li id="r3">` a `:target` style makes clicking a citation highlight its
source. That is the whole mechanism.

### The smallest template that works

```html
<!doctype html><meta charset="utf-8"><title>{{title}}</title>
<style>
  @page { size: A4; margin: 20mm; }
  body { font: 11pt/1.6 Georgia, serif; color: #16181d; max-width: 46em; margin: auto; }
  h1 { color: {{accent}}; }
  .cite { color: {{accent}}; text-decoration: none; }
  ol.refs li:target { background: color-mix(in srgb, {{accent}} 14%, transparent); }
</style>
<h1>{{title}}</h1>
{{#author}}<p class="by">{{author}}{{#org}} — {{org}}{{/org}}</p>{{/author}}
<p class="meta">{{date}} · {{count_points}} points · {{count_sources}} sources</p>
{{#summary}}<p class="abstract">{{summary}}</p>{{/summary}}
{{#toc}}{{toc}}{{/toc}}
{{body}}
{{#references}}<h2>References</h2><ol class="refs">{{references}}</ol>{{/references}}
{{#figures}}<h2>Figures</h2>{{figures}}{{/figures}}
<footer>{{footer}}</footer>
```

---

## 4. Designing for print

PDF is produced by printing your HTML with headless Chromium, so print CSS is
real CSS and it works:

- `@page { size: A4; margin: 18mm 16mm 20mm; }` — Trailmark passes
  `--no-pdf-header-footer`, so your margins are the only margins.
- `break-inside: avoid` on figures, tables and callouts.
- `h2 { break-after: avoid; }` so a heading never ends a page alone.
- `@media print { nav.toc { position: static; } }` — anything sticky must be
  unstuck for print.
- Background fills and coloured blocks need `print-color-adjust: exact` (plus the
  `-webkit-` prefix) on the elements that carry them, or Chromium may drop them.

Web fonts are not fetched — the render is offline and a missing font silently
falls back. Use a system stack, or embed the font as a `data:` URI in the folder.

---

## 5. The LaTeX path (optional)

Add `template.tex` and put `latex` in `formats`. Trailmark writes the filled
`.tex` **always**, then tries `typst` → `tectonic` → `xelatex` → `pdflatex`. If
none is installed you still get the `.tex` to build wherever you like, and the
PDF falls back to the HTML path.

In `.tex`, `{{body}}` arrives as LaTeX, not HTML: `\textbf{}`, `\textit{}`,
`\texttt{}`, `\section{}`, `itemize`, and citations as `\cite{ref3}`. Reference
entries are `\bibitem{ref3}`. Colour comes in as
`\definecolor{accent}{HTML}{{{accent_hex}}}`.

Use it when you want real journal typesetting — proper hyphenation, float
placement, microtype. For everything else the HTML path is faster and looks the
same.

---

## 6. Testing

Log two or three points against a scratch topic, export, and look at the file.
That is the whole loop; it takes seconds. The export dialog reports the engine
that rendered the PDF and its page count, and refuses a PDF that came out under
1200 bytes or with no pages — so a template that fails to render tells you so
instead of handing you a blank page.

If the PDF is blank and the HTML is fine, the usual cause is a `position: fixed`
element covering the page or an `@page` size smaller than the content box.

---

## 7. Asking an AI to write it for you

Paste this, with your own answers filled into the four bracketed lines. It
produces a complete folder in one shot.

> You are writing a document template for Trailmark, a research-logging desktop
> app. A template is a folder containing `template.json` and `template.html`.
> `template.html` is a standalone HTML page that will be filled in and then
> printed to PDF by headless Chromium, so it must use print CSS (`@page`,
> `break-inside`, `break-after`) and must not rely on JavaScript, on network
> requests, or on web fonts.
>
> Fill the page using these placeholders and no others. `{{name}}` inserts a
> value; `{{#name}}…{{/name}}` keeps its contents only when the value is
> non-empty and deletes them otherwise — wrap every optional region that way.
>
> `{{title}}` `{{subtitle}}` `{{kicker}}` `{{author}}` `{{org}}` `{{date}}`
> `{{date_iso}}` `{{period}}` `{{body}}` `{{toc}}` `{{references}}`
> `{{figures}}` `{{summary}}` `{{count_points}}` `{{count_sources}}`
> `{{footer}}` `{{accent}}` `{{app_version}}`
>
> `{{body}}` arrives as HTML containing `<h2 id="s-...">`, `<h3>`, `<p>`,
> `<ul>`, `<ol>`, `<blockquote>`, `<pre><code>`, `<strong>`, `<em>`, and
> citation links shaped `<a class="cite" href="#r3">[3]</a>`. `{{references}}`
> arrives as bare `<li id="r3">…</li>` items that you must place inside your own
> `<ol>`. `{{toc}}` arrives as a complete `<nav><ol>…</ol></nav>`. `{{figures}}`
> arrives as `<figure><img><figcaption>` blocks.
>
> Also write `template.json` with the keys: `id`, `name`, `purpose`,
> `description`, `kicker`, `accent` (one hex colour), `formats` (a subset of
> `["html","pdf","markdown","docx"]`), and `page` (`{"size":…,"margin":…}`).
>
> The template is for: **[what kind of document, and who reads it]**
> It should feel: **[three adjectives — e.g. quiet, dense, authoritative]**
> Page size and margins: **[A4 / Letter, and margins]**
> Non-negotiables: **[e.g. must fit on one page; must show the source count on
> the cover; must be legible photocopied in black and white]**
>
> Commit to one visual direction rather than offering options. Put all CSS in a
> single `<style>` block at the top of the file. Return the two files complete,
> with no explanation between them.

Then drop the two files in `%APPDATA%\Trailmark\templates\<id>\`, open the
export dialog, and export. If it looks wrong, paste the PDF back at the model
and say what is wrong — the loop is short enough that this is faster than
reading CSS.

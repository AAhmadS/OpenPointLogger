import json
import urllib.request

from point_store import PROVIDERS


def resolve_base_url(cfg):
    base = (cfg.get("base_url") or "").strip().rstrip("/")
    if base:
        return base
    return PROVIDERS.get(cfg.get("provider"), PROVIDERS["openrouter"])["base_url"].rstrip("/")


def chat(cfg, system, user, timeout=90):
    if not cfg.get("enabled"):
        return {"error": "AI assist is disabled. Enable it in Settings and add your API key."}
    api_key = (cfg.get("api_key") or "").strip()
    if not api_key:
        return {"error": "No API key set. Open Settings → AI assist and paste your key."}
    model = (cfg.get("model") or "").strip() or PROVIDERS.get(cfg.get("provider"), {}).get("model", "")
    if not model:
        return {"error": "No model configured."}
    base = resolve_base_url(cfg)
    provider = (cfg.get("provider") or "").strip()
    is_google = provider == "google" or "generativelanguage.googleapis.com" in base
    if is_google and not base.endswith("/openai"):
        # Google Gemini native endpoint
        # url: https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent
        url = "%s/models/%s:generateContent" % (base.rstrip("/"), model)
        body = json.dumps({
            "systemInstruction": {"parts": [{"text": system}]},
            "contents": [{"role": "user", "parts": [{"text": user}]}],
            "generationConfig": {"temperature": 0.3},
        }).encode("utf-8")
        req = urllib.request.Request(url, data=body, headers={
            "x-goog-api-key": api_key,
            "Content-Type": "application/json",
        })
    else:
        # OpenAI-compatible (OpenAI, OpenRouter, Mistral, AvalAI, Google-openai compat)
        url = "%s/chat/completions" % base
        body = json.dumps({
            "model": model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "temperature": 0.3,
        }).encode("utf-8")
        hdrs = {
            "Authorization": "Bearer %s" % api_key,
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/AAhmadS/trailmark",
            "X-Title": "Trailmark",
        }
        if is_google:
            hdrs["x-goog-api-key"] = api_key
        req = urllib.request.Request(url, data=body, headers=hdrs)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        try:
            detail = e.read().decode("utf-8")
        except Exception:
            detail = ""
        return {"error": "Provider returned HTTP %s: %s" % (e.code, detail[:300])}
    except Exception as e:
        return {"error": "Request failed: %s" % e}
    try:
        if is_google and not (base.endswith("/openai") if 'base' in locals() else False):
            # Google response: candidates[0].content.parts[0].text
            content = data["candidates"][0]["content"]["parts"][0]["text"]
        else:
            content = data["choices"][0]["message"]["content"]
        return {"content": content}
    except Exception as e:
        return {"error": "Unexpected provider response: %s" % e}


def test_connection(cfg):
    if not (cfg.get("api_key") or "").strip():
        return {"error": "Add an API key first."}
    res = chat(cfg, "You are a connectivity test. Reply with exactly: OK",
               "Reply with OK.")
    if res.get("content"):
        return {"ok": True, "reply": res["content"]}
    return {"ok": False, "error": res.get("error", "No response.")}


def polish_entry(cfg, text):
    system = ("You clean up research notes. Keep the meaning and every factual claim exactly "
              "as written. Fix grammar and typos, tighten phrasing, remove redundancy, and "
              "return only the cleaned note — no headings, no quotes, no commentary.")
    return chat(cfg, system, "Clean up this research note:\n\n%s" % text)


def draft_summary(cfg, topic_title, subtopics_text, max_points):
    system = ("You write concise research summaries. Be neutral, precise, and faithful to the "
              "given points. Do not invent facts, sources, or citations. Return a short "
              "plain-text summary in a few sentences.")
    user = ("Summarize the research topic \"%s\" based on these logged points "
            "(at most %d points, grouped by sub-topic):\n\n%s") % (topic_title, max_points, subtopics_text)
    return chat(cfg, system, user)


def polish_report(cfg, topic_title, composed_markdown):
    """Rewrite an already-composed Markdown report, returning Markdown.

    The contract changed when export became a pipeline: the model no longer sees
    raw points and no longer decides layout. It receives the Markdown the
    deterministic composer produced and returns Markdown of the same shape. The
    citation grounding gate downstream rejects the result if [n] markers were
    invented or silently dropped, so the prompt says so plainly rather than
    leaving the model to guess what will be checked.
    """
    system = "\n".join([
        "You are a research editor. You will be given a report that is ALREADY in Markdown.",
        "Return the improved report as Markdown and nothing else - no preamble, no code fence,",
        "no HTML, no commentary.",
        "Rules:",
        "- Do not change facts, claims, numbers, names or meaning. Fix grammar, typos and phrasing.",
        "- Keep every citation exactly as [n] with its original number. Never renumber, never invent",
        "  a number, never drop one. A citation you add or remove is rejected automatically.",
        "- You may merge, split, reorder and retitle sections, and turn a run of related points into",
        "  a paragraph. Use ## for sections and ### for sub-sections.",
        "- Markdown you may use: ## headers, paragraphs, - bullets, 1. numbered lists, **bold**,",
        "  *italic*, `code`, > blockquotes and [text](url) links. Nothing else: no table of contents,",
        "  no front matter, no title line (the template supplies the title), no horizontal rules.",
        "- Keep the tone neutral and precise.",
    ])
    user = "\n".join(["Topic: %s" % topic_title, "", "Report to polish:", "",
                      composed_markdown, "", "Return the polished report as Markdown."])
    return chat(cfg, system, user, timeout=120)
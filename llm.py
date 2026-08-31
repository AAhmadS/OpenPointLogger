import json
import urllib.request

from point_store import PROVIDERS


def resolve_base_url(cfg):
    base = (cfg.get("base_url") or "").strip().rstrip("/")
    if base:
        return base
    return PROVIDERS.get(cfg.get("provider"), PROVIDERS["openrouter"])["base_url"].rstrip("/")


def chat(cfg, system, user, timeout=60):
    if not cfg.get("enabled"):
        return {"error": "AI assist is disabled. Enable it in Settings and add your API key."}
    api_key = (cfg.get("api_key") or "").strip()
    if not api_key:
        return {"error": "No API key set. Open Settings → AI assist and paste your key."}
    model = (cfg.get("model") or "").strip() or PROVIDERS.get(cfg.get("provider"), {}).get("model", "")
    if not model:
        return {"error": "No model configured."}
    base = resolve_base_url(cfg)
    url = "%s/chat/completions" % base
    body = json.dumps({
        "model": model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "temperature": 0.3,
    }).encode("utf-8")
    req = urllib.request.Request(url, data=body, headers={
        "Authorization": "Bearer %s" % api_key,
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com/AAhmadS/trailmark",
        "X-Title": "Trailmark",
    })
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
        content = data["choices"][0]["message"]["content"]
        return {"content": content}
    except Exception:
        return {"error": "Unexpected provider response."}


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
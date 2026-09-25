"""Re-run the labelled cases that set the thresholds in judge.py.

This is not part of the test suite. It needs a key and a network, it costs a
few cents, and it talks to a versioned model that may move - which is exactly
why the numbers it produces have to be reproducible rather than remembered.

    set TYPESAFE_API_KEY=...        (or ~/.claude/secrets/typesafe_api_key)
    .venv/Scripts/python.exe evals/judge_eval.py
    .venv/Scripts/python.exe evals/judge_eval.py --model jev-latest

It drives judge.QUESTIONS and the criteria dicts directly. That matters: an
eval with its own copy of the question measures a question nobody ships.

Exit 0 every case matched its label - 1 at least one did not - 2 the eval could
not run at all (no key, no network). Two is UNRESOLVED, never a pass.

The cases were written by Claude while building the feature, which is a real
limitation and is recorded as one in .claude/gates/jev-integration.yaml: they
test whether the question separates cases the author already had in mind, not
whether it survives how this app is actually used.
"""

import argparse
import json
import os
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

import judge  # noqa: E402

CASES = pathlib.Path(__file__).resolve().parent / "judge_cases.json"


def find_key():
    """The key by location, never by value. Returns (key, where)."""
    env = (os.environ.get("TYPESAFE_API_KEY") or "").strip()
    if env:
        return env, "TYPESAFE_API_KEY"
    path = pathlib.Path.home() / ".claude" / "secrets" / "typesafe_api_key"
    if path.exists():
        text = path.read_text(encoding="utf-8").strip()
        if text:
            return text, str(path)
    return "", "not found in TYPESAFE_API_KEY or ~/.claude/secrets/typesafe_api_key"


def build_notes(cases):
    state = {"cases": [{"my_note": c["my_note"], "draft_passage": c["draft_passage"]}
                       for c in cases]}
    qs = {"case_%02d" % n: {"type": "choice",
                            "instructions": judge.QUESTIONS["note_survived"].format(i=n),
                            "criteria": judge.NOTE_CRITERIA}
          for n in range(len(cases))}
    return state, qs, "case_%02d"


def build_kinds(cases):
    state = {"captures": [{"text": c["text"],
                           "a_source_is_attached": bool(c["a_source_is_attached"])}
                          for c in cases]}
    qs = {"cap_%02d" % n: {"type": "choice",
                           "instructions": judge.QUESTIONS["capture_kind"].format(i=n),
                           "criteria": judge.KIND_CRITERIA}
          for n in range(len(cases))}
    return state, qs, "cap_%02d"


def band(label, cfg, cases, builder):
    state, qs, fmt = builder(cases)
    payload = judge.ask(cfg, state, qs, timeout=40)
    if not payload:
        print("  UNRESOLVED - the request returned nothing. Not a pass.")
        return None
    answers = payload.get("answers") or {}
    print("  model=%s  cases=%d" % (payload.get("model"), len(cases)))
    rows, wrong = [], 0
    for n, c in enumerate(cases):
        a = answers.get(fmt % n) or {}
        got, conf = a.get("choice"), a.get("confidence")
        ok = got == c["label"]
        wrong += not ok
        drift = ""
        was = (c.get("observed") or {}).get("confidence")
        if isinstance(conf, (int, float)) and isinstance(was, (int, float)):
            if abs(conf - was) >= 0.15:
                drift = "  (was %.2f)" % was
        print("  %-14s %-9s want %-9s conf %s  %s%s   %s"
              % (c["id"], got, c["label"],
                 ("%.2f" % conf) if isinstance(conf, (int, float)) else "----",
                 c["lang"], drift, "" if ok else "<<< MISMATCH"))
        rows.append({"id": c["id"], "label": c["label"], "got": got,
                     "confidence": conf, "lang": c["lang"], "ok": ok})
    print("  %s: %d/%d correct" % (label, len(cases) - wrong, len(cases)))
    return rows


def thresholds(rows):
    """Re-derive what the thresholds have to be, from this run's numbers.

    The point of printing this is that the numbers in judge.THRESHOLDS stop
    being opinions. Each has a case that binds it, and if a model update moves
    that case, the next run says so instead of failing quietly.
    """
    def conf(r):
        c = r.get("confidence")
        return c if isinstance(c, (int, float)) else 0.0

    pres = [r for r in rows if r["label"] == "preserved" and r["ok"]]
    flag = [r for r in rows if r["label"] in ("altered", "missing") and r["ok"]]
    print()
    print("-- what these numbers imply for the thresholds --")
    if flag:
        low = min(flag, key=conf)
        print("  note_flag_min must be <= %.2f to keep %s (%s); currently %.2f"
              % (conf(low), low["id"], low["label"],
                 judge.THRESHOLDS["note_flag_min"]))
        missed = [r for r in flag if conf(r) < judge.THRESHOLDS["note_flag_min"]]
        print("  flags lost at the current threshold: %d" % len(missed))
        for r in missed:
            print("    %s at %.2f - falls back to the substring check"
                  % (r["id"], conf(r)))
    if pres:
        over = judge.THRESHOLDS["note_preserved_overturn"]
        rescued = [r for r in pres if conf(r) >= over]
        print("  preserved cases clearing %.2f: %d of %d"
              % (over, len(rescued), len(pres)))
        for r in pres:
            if conf(r) < over:
                print("    %s at %.2f - correct, but not confident enough to"
                      " overturn, so the user still sees a spurious"
                      " 'note is missing' finding" % (r["id"], conf(r)))
    kinds = [r for r in rows if r["label"] in ("note", "claim", "quote") and r["ok"]]
    if kinds:
        km = judge.THRESHOLDS["capture_kind_min"]
        below = [r for r in kinds if conf(r) < km]
        print("  kind answers below %.2f: %d of %d (each keeps the default %r)"
              % (km, len(below), len(kinds), judge.KIND_FALLBACK))
        for r in below:
            print("    %s at %.2f" % (r["id"], conf(r)))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="", help="override judge.MODEL for this run")
    ap.add_argument("--base-url", default="")
    ap.add_argument("--out", default="", help="write the raw rows here as JSON")
    args = ap.parse_args()

    doc = json.loads(CASES.read_text(encoding="utf-8"))
    key, where = find_key()
    print("key: %s" % where)
    if not key:
        print("UNRESOLVED - no key, so nothing was measured. Exit 2.")
        return 2
    cfg = {"enabled": True, "api_key": key,
           "model": args.model or judge.MODEL, "base_url": args.base_url}
    print("model requested: %s" % cfg["model"])
    print("cases recorded %s against %s" % (doc["measured_at"], doc["model"]))
    print()

    all_rows = []
    for sub in ("clean", "adversarial"):
        part = [c for c in doc["notes"] if c["band"] == sub]
        print("-- %s notes (%d) --" % (sub, len(part)))
        rows = band(sub, cfg, part, build_notes)
        if rows is None:
            return 2
        all_rows += rows
        print()

    print("-- capture kinds (%d) --" % len(doc["kinds"]))
    rows = band("kinds", cfg, doc["kinds"], build_kinds)
    if rows is None:
        return 2
    all_rows += rows
    print()

    thresholds(all_rows)
    bad = [r for r in all_rows if not r["ok"]]
    print()
    print("TOTAL: %d/%d correct" % (len(all_rows) - len(bad), len(all_rows)))
    fa = [r for r in all_rows if r["lang"] == "fa"]
    if fa:
        print("Persian band: %d/%d correct, confidence %.2f-%.2f"
              % (sum(1 for r in fa if r["ok"]), len(fa),
                 min((r["confidence"] or 0) for r in fa),
                 max((r["confidence"] or 0) for r in fa)))
    if args.out:
        pathlib.Path(args.out).write_text(
            json.dumps(all_rows, ensure_ascii=False, indent=2), encoding="utf-8")
        print("rows written to %s" % args.out)
    if bad:
        print("MISMATCHES: " + ", ".join(r["id"] for r in bad))
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())

"""Re-run the labelled utterances that set the two command thresholds in judge.py.

Not part of the test suite, for the same reasons as judge_eval.py: it needs a
key and a network, and it talks to a versioned model.

    .venv/Scripts/python.exe evals/command_eval.py
    .venv/Scripts/python.exe evals/command_eval.py --runs 2 --out rows.json

Every case goes through voicecmd.parse first, and the runner refuses a case
that does not parse to a form needing an opinion - a case that never reaches
the question in the app measures nothing. The request is judge.command_request,
the one the app sends.

The question is a Noul (P(yes)): is what follows "session"/"tab" a name?
What it prints at the end is the band the threshold may sit in:
  * the LOWEST P(yes) on a real command (the bar must be at or below it, or
    real commands are lost), and
  * the HIGHEST P(yes) on dictation (the bar must be above it, or dictation
    gets executed).
If the second is not below the first, no threshold separates them and the
runner says so.

Cases marked ``reaches: code`` are checked against the parser only, with no
call. A ``known_miss`` among them (a command said at the end of a sentence)
is printed, not failed: it is the documented cost of a form that was dropped.

Exit 0 every asked case correct on every run - 1 at least one mistake - 2
could not run (no key, no network). Two is UNRESOLVED, never a pass.
"""

import argparse
import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE))

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

import trailmark.judge as judge
import trailmark.voicecmd as voicecmd
from judge_eval import find_key  # noqa: E402

CASES = HERE / "command_cases.json"


def parsed_cases(doc):
    """Split the band into what reaches the question and what code decides.

    A case marked ``reaches: code`` must NOT parse to a question - it is the
    evidence for a rule code applies on its own (no pause mark before a
    trailing word means dictation). Every other case must parse to one.
    """
    asked, decided, bad = [], [], []
    for c in doc["cases"]:
        p = voicecmd.parse(c["text"])
        if c.get("reaches") == "code":
            d = voicecmd.decide(p, None)
            if p["form"] in voicecmd.OPINION_FORMS or d["action"] != "text":
                bad.append("%s should be decided by code as text, parses as form=%s"
                           % (c["id"], p["form"]))
                continue
            decided.append(c)
            continue
        if p["form"] not in voicecmd.OPINION_FORMS or p["command"] != c["command"]:
            bad.append("%s parses as form=%s command=%s"
                       % (c["id"], p["form"], p["command"]))
            continue
        asked.append((c, p))
    return asked, decided, bad


def _one(cfg, parsed):
    """One request with ONE utterance in the state - the shape the app sends.

    Batching every case into one state is cheaper, and it measured something
    else: with 47 utterances in the state the same questions lost the Persian
    band and most of the trailing margin. A judgement over a large state is on
    Jev's documented weak list, and the app never builds one.
    """
    import time
    state, qs = judge.command_request([parsed])
    for attempt in range(4):
        payload = judge.ask(cfg, state, qs, timeout=60)
        if payload:
            return (judge._noul(payload.get("answers") or {}, "utt_00"),
                    payload.get("model") or "")
        time.sleep(1.5 * (attempt + 1))   # judge.ask hides the status; assume 429
    return None, ""


def run_once(cfg, cases):
    from concurrent.futures import ThreadPoolExecutor
    with ThreadPoolExecutor(max_workers=2) as pool:
        got = list(pool.map(lambda cp: _one(cfg, cp[1]), cases))
    if any(m == "" for _, m in got):
        return None, ""
    rows = []
    for (c, p), (pyes, _) in zip(cases, got):
        t = judge.command_threshold(p["form"])
        answer = None if pyes is None else ("command" if pyes >= t else "text")
        rows.append({"id": c["id"], "lang": c["lang"], "form": p["form"],
                     "label": c["label"], "got": answer, "p_yes": pyes,
                     "ok": answer == c["label"]})
    return rows, sorted(set(m for _, m in got))[0]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="")
    ap.add_argument("--runs", type=int, default=2)
    ap.add_argument("--out", default="")
    args = ap.parse_args()

    doc = json.loads(CASES.read_text(encoding="utf-8"))
    cases, decided, bad = parsed_cases(doc)
    if bad:
        print("CASE ERRORS - these never reach the question in the app:")
        for b in bad:
            print("  " + b)
        return 1
    key, where = find_key()
    print("key: %s" % where)
    if not key:
        print("UNRESOLVED - no key, so nothing was measured. Exit 2.")
        return 2
    cfg = {"enabled": True, "api_key": key, "model": args.model or judge.MODEL}
    print("model requested: %s   asked: %d   decided by code: %d   runs: %d"
          % (cfg["model"], len(cases), len(decided), args.runs))
    print()
    print("-- decided by code, never asked --")
    for c in decided:
        print("  %-15s text     want %-7s %s" % (c["id"], c["label"],
              ("known miss: " + c["known_miss"]) if c.get("known_miss") else ""))

    runs = []
    for r in range(args.runs):
        rows, model = run_once(cfg, cases)
        if rows is None:
            print("UNRESOLVED - run %d returned nothing. Not a pass." % (r + 1))
            return 2
        print()
        print("-- run %d  model=%s --" % (r + 1, model))
        for row in rows:
            print("  %-15s %-8s %-3s P(yes) %s -> %-7s want %-7s %s"
                  % (row["id"], row["form"], row["lang"],
                     ("%.2f" % row["p_yes"]) if row["p_yes"] is not None else "----",
                     row["got"], row["label"], "" if row["ok"] else "<<< MISTAKE"))
        runs.append(rows)

    all_rows = [row for rows in runs for row in rows]
    print()
    print("-- what these numbers allow --")
    for form, key_ in (("argument", "command_name_min"),):
        part = [r for r in all_rows if r["form"] == form and r["p_yes"] is not None]
        cmd = [r["p_yes"] for r in part if r["label"] == "command"]
        txt = [r["p_yes"] for r in part if r["label"] != "command"]
        t = judge.THRESHOLDS[key_]
        line = "  %-8s  commands %s  dictation %s  threshold %.2f" % (
            form,
            ("%.2f-%.2f" % (min(cmd), max(cmd))) if cmd else "none",
            ("%.2f-%.2f" % (min(txt), max(txt))) if txt else "none", t)
        print(line)
        if cmd and txt:
            if max(txt) >= min(cmd):
                print("            NO threshold separates them.")
            else:
                print("            margin: %.2f above the highest dictation, %.2f below the"
                      " lowest command" % (t - max(txt), min(cmd) - t))
        for lang in ("en", "fa"):
            lp = [r for r in part if r["lang"] == lang]
            if lp:
                print("            %s: %d/%d correct" % (lang, sum(r["ok"] for r in lp), len(lp)))
    if len(runs) > 1:
        drift = [abs(a["p_yes"] - b["p_yes"]) for a, b in zip(runs[0], runs[1])
                 if a["p_yes"] is not None and b["p_yes"] is not None]
        if drift:
            print("  run-to-run drift: mean %.3f  max %.3f"
                  % (sum(drift) / len(drift), max(drift)))
    wrong = [r for r in all_rows if not r["ok"]]
    print()
    print("TOTAL: %d/%d correct across %d run(s)"
          % (len(all_rows) - len(wrong), len(all_rows), len(runs)))
    if args.out:
        pathlib.Path(args.out).write_text(json.dumps(runs, ensure_ascii=False, indent=2),
                                          encoding="utf-8")
        print("rows written to %s" % args.out)
    if wrong:
        print("MISTAKES: " + ", ".join(sorted(set(r["id"] for r in wrong))))
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())

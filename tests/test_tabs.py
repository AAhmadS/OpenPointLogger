"""Headless tests for tab (sub-topic) removal and rename.

Pins the resurrection bug: deleting a tab removed it from the store, but
the draft still addressed the old name, so the next logged point re-created
the tab through add_entry's auto-append - from the user's chair, the tab
could not be removed. Renaming had the identical hole.

Drives the real Api + Controller against a temp-APPDATA Store. No
microphone, no network, no windows.

Run:  PYTHONPATH=. .venv/Scripts/python.exe tests/test_tabs.py
"""

import pathlib
import sys
import tempfile

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

FAILS = []


def check(label, ok, detail=""):
    print(("  PASS  " if ok else "  FAIL  ") + label + (" - %s" % (detail,) if detail else ""))
    if not ok:
        FAILS.append(label)


import trailmark.point_store as ps  # noqa: E402

tmp = pathlib.Path(tempfile.mkdtemp(prefix="opl_tabs_"))
ps.BASE_DIR = tmp
ps.DATA_FILE = tmp / "points.json"
ps.CONFIG_FILE = tmp / "config.json"
ps.ATTACH_DIR = tmp / "attachments"
ps.EXPORT_DIR = tmp / "exports"

import point_logger  # noqa: E402


def fresh():
    c = point_logger.Controller()
    c.refresh_full = lambda: None
    pushes = []
    c.push_voice_state = lambda s, d="": pushes.append((s, d))
    api = point_logger.Api(c.store, c)
    return c, api, pushes


def new_topic_with_tab(c, api, tab="intro"):
    t = c.store.start_topic("T")
    tid = t["topics"][0]["id"]
    api.add_subtopic(tid, tab)
    return tid


# ---------------------------------------------------------------------------
# 1. Delete clears a draft addressed at the tab; the tab stays deleted
# ---------------------------------------------------------------------------
print("\n-- delete --")

c, api, pushes = fresh()
tid = new_topic_with_tab(c, api)
c.draft.set_meta({"topic_id": tid, "subtopic": "intro"})
c.draft.append("first point", origin="voice")
c.run_voice_command("log")
check("point filed under the tab",
      c.store.find_topic(tid)["entries"][-1]["subtopic"] == "intro")

r = api.delete_subtopic(tid, "intro")
check("delete reports no error", not r.get("error"), r.get("error"))
check("tab gone from the store", "intro" not in c.store.find_topic(tid)["subtopics"])
check("filed point moved back to General",
      c.store.find_topic(tid)["entries"][-1]["subtopic"] == "")
check("draft retargeted to General",
      c.draft.meta() == {"topic_id": tid, "subtopic": "", "kind": ""}, c.draft.meta())
check("windows told the draft moved", ("edited", "") in pushes, pushes)

c.draft.append("second point", origin="voice")
c.run_voice_command("log")
check("the next log does not resurrect the tab",
      "intro" not in c.store.find_topic(tid)["subtopics"],
      c.store.find_topic(tid)["subtopics"])
check("both points kept, both under General",
      [(e["text"], e["subtopic"]) for e in c.store.find_topic(tid)["entries"]] ==
      [("first point", ""), ("second point", "")],
      [(e["text"], e["subtopic"]) for e in c.store.find_topic(tid)["entries"]])


# ---------------------------------------------------------------------------
# 2. Delete leaves other drafts alone
# ---------------------------------------------------------------------------
print("\n-- delete spares other drafts --")

c, api, pushes = fresh()
tid = new_topic_with_tab(c, api)
t2 = c.store.start_topic("T2")
tid2 = t2["topics"][-1]["id"]
api.add_subtopic(tid2, "intro")  # same name, other topic
c.draft.set_meta({"topic_id": tid2, "subtopic": "intro"})
api.delete_subtopic(tid, "intro")
check("a same-named tab in another topic keeps its draft address",
      c.draft.meta() == {"topic_id": tid2, "subtopic": "intro", "kind": ""}, c.draft.meta())
check("no push for an untouched draft", ("edited", "") not in pushes, pushes)

c.draft.set_meta({"topic_id": tid, "subtopic": ""})
api.delete_subtopic(tid, "missing")
check("deleting a missing tab is a silent no-op", True)


# ---------------------------------------------------------------------------
# 3. Rename moves the draft along; empty rename changes nothing
# ---------------------------------------------------------------------------
print("\n-- rename --")

c, api, pushes = fresh()
tid = new_topic_with_tab(c, api)
c.draft.set_meta({"topic_id": tid, "subtopic": "intro"})
c.draft.append("under intro", origin="voice")
c.run_voice_command("log")
r = api.rename_subtopic(tid, "intro", "background")
check("rename reports no error", not r.get("error"), r.get("error"))
check("old name gone, new name listed",
      c.store.find_topic(tid)["subtopics"] == ["background"],
      c.store.find_topic(tid)["subtopics"])
check("filed point renamed too",
      c.store.find_topic(tid)["entries"][-1]["subtopic"] == "background")
check("draft follows the rename",
      c.draft.meta()["subtopic"] == "background", c.draft.meta())
c.draft.append("after rename", origin="voice")
c.run_voice_command("log")
check("the next log files under the new name and revives nothing old",
      c.store.find_topic(tid)["subtopics"] == ["background"] and
      c.store.find_topic(tid)["entries"][-1]["subtopic"] == "background")

r = api.rename_subtopic(tid, "background", "  ")
check("renaming to blank errors", bool(r.get("error")), r)
check("a failed rename leaves the draft where it was",
      c.draft.meta()["subtopic"] == "background", c.draft.meta())


print()
print("ALL CHECKS PASSED" if not FAILS else "FAILED: " + ", ".join(FAILS))
sys.exit(1 if FAILS else 0)

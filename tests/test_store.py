import base64
import pathlib
import tempfile

import trailmark.point_store as ps

tmp = pathlib.Path(tempfile.mkdtemp(prefix="opl_test_"))
ps.BASE_DIR = tmp
ps.DATA_FILE = tmp / "points.json"
ps.CONFIG_FILE = tmp / "config.json"
ps.ATTACH_DIR = tmp / "attachments"
ps.EXPORT_DIR = tmp / "exports"

s = ps.Store()
r = s.start_topic("Rust borrow checker")
tid = r["topics"][0]["id"]
assert not r.get("error"), r
s.add_subtopic(tid, "Ownership")
png = base64.b64encode(
    bytes.fromhex(
        "89504e470d0a1a0a0000000d49484452000000010000000108060000001f15c489"
        "0000000d49444154789c6360000002000100ffff03000006000557bfabd4000000"
        "0049454e44ae426082"
    )
).decode()
s.add_entry(tid, "Ownership",
            "The borrow checker enforces ownership rules at compile time.",
            "https://doc.rust-lang.org/book/ch04-01-what-is-ownership.html", "", None)
s.add_entry(tid, "Ownership",
            "A reference does not take ownership.",
            "", 'The Rust Programming Language, ch. 4',
            "data:image/png;base64," + png)
s.add_entry(tid, "",
            "Borrowing rules prevent data races.",
            "https://doc.rust-lang.org/book/ch04-02-references-and-borrowing.html", "", None)
s.close_topic(tid)
ex = s.export_topic(tid)
assert not ex.get("error"), ex
html = pathlib.Path(ex["html"]).read_text(encoding="utf-8")
md = pathlib.Path(ex["md"]).read_text(encoding="utf-8")
# the export goes through the template pipeline now, so the source list is
# whatever the chosen template calls it - what has to hold is that every
# reference got an anchor and every citation points at one.
assert 'id="r1"' in html and 'id="r2"' in html
assert "References" in md
assert "Ownership" in html
assert "<img" in html
assert html.count('class="cite"') == 4
assert "[1]" in md and "[2]" in md
print("EXPORT OK ->", ex["folder"])
print("points.json entries:", len(s.state()["topics"][0]["entries"]))
print("html size", len(html), "md size", len(md))

s.reopen_topic(tid)
assert s.state()["topics"][0]["status"] == "open"
s.delete_topic(tid)
assert s.state()["topics"] == []
print("open/reopen/delete OK")

cfg = s.config
assert cfg["llm"]["provider"] == "openrouter"
assert cfg["llm"]["model"] == "deepseek/deepseek-v4-flash"
assert cfg["hotkey"] == {"modifiers": ["ctrl", "alt"], "key": "P"}
print("config defaults OK")

# --- categories ---------------------------------------------------------
#
# The create/rename/slugify logic lives on point_logger.Api (not on Store
# itself - the spec places it there), so exercising it needs an Api instance.
# This test file only ever builds a bare Store(), so a minimal controller
# stand-in is constructed inline here, just enough to satisfy Api's calls
# into `self.controller.refresh_full()` without a real webview window.
import point_logger as point_logger


class _StubController:
    def refresh_full(self):
        pass


items = s.config["categories"]["items"]
assert [c["id"] for c in items] == ["research", "business", "team", "personal"]
assert [c["name"] for c in items] == ["Research", "Business", "Team", "Personal"]
assert [c["default_template"] for c in items] == [
    "research-roam", "business-formal", "team-report", "personal-report"]
print("categories defaults OK")

api = point_logger.Api(s, _StubController())

# create: a brand-new category, valid default_template. business-formal /
# team-report are deliberately avoided here (a parallel worker is still
# landing those template folders) in favour of the three templates already
# guaranteed to exist.
r = api.save_category({"name": "Side Projects", "default_template": "personal-report"})
assert not r.get("error"), r
new_cat = next(c for c in r["categories"] if c["name"] == "Side Projects")
assert new_cat["id"] == "side-projects"
assert new_cat["default_template"] == "personal-report"
assert new_cat["count"] >= 0
print("save_category create OK ->", new_cat["id"])

# create with an unresolvable default_template must be refused, unchanged
before = len(s.config["categories"]["items"])
r = api.save_category({"name": "Bogus", "default_template": "no-such-template"})
assert r.get("error"), r
assert len(s.config["categories"]["items"]) == before
print("save_category create rejects unknown template OK")

# rename: existing id, change name and default_template
r = api.save_category({"id": "side-projects", "name": "Side Quests",
                        "default_template": "research-roam"})
assert not r.get("error"), r
renamed = next(c for c in s.config["categories"]["items"] if c["id"] == "side-projects")
assert renamed["name"] == "Side Quests"
assert renamed["default_template"] == "research-roam"
print("save_category rename OK")

# duplicate display name -> the second create gets a -2 suffix id (this
# repo's dedup-by-suffix policy; see point_logger.Api.save_category)
r1 = api.save_category({"name": "Notes", "default_template": "personal-report"})
assert not r1.get("error"), r1
r2 = api.save_category({"name": "Notes", "default_template": "personal-report"})
assert not r2.get("error"), r2
notes_ids = sorted(c["id"] for c in s.config["categories"]["items"] if c["name"] == "Notes")
assert notes_ids == ["notes", "notes-2"], notes_ids
print("save_category duplicate-name suffix OK ->", notes_ids)

# delete_category refuses once only one category remains
all_ids = [c["id"] for c in s.config["categories"]["items"]]
for cid in all_ids[:-1]:
    r = api.delete_category(cid)
    assert not r.get("error"), r
assert len(s.config["categories"]["items"]) == 1
last_id = s.config["categories"]["items"][0]["id"]
r = api.delete_category(last_id)
assert r.get("error"), r
assert len(s.config["categories"]["items"]) == 1
print("delete_category refuses last-category OK")

# set_category_default round-trip through a *fresh* Store() reload - the
# single most likely regression is forgetting to add "categories" to the
# merge tuple in Store._load_config, which would silently drop this on the
# next launch instead of merely leaving it unsaved in memory.
r = api.set_category_default(last_id, "research-roam")
assert not r.get("error"), r
s.save_config()

s2 = ps.Store()
reloaded = next(c for c in s2.config["categories"]["items"] if c["id"] == last_id)
assert reloaded["default_template"] == "research-roam", reloaded
print("set_category_default survives reload OK")

# template_demo works against a pre-existing template
r = api.template_demo("personal-report")
assert not r.get("error"), r
assert "<html" in r["html"].lower() or "<!doctype" in r["html"].lower()
assert "Rust borrow checker" in r["html"]
print("template_demo OK, html size", len(r["html"]))

r = api.template_demo("no-such-template")
assert r.get("error"), r
print("template_demo unknown-id error OK")

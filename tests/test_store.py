import base64
import pathlib
import tempfile

import point_store as ps

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
assert "References" in html and "References" in md
assert "Ownership" in html
assert "<img" in html
assert html.count('<sup class="cite">') == 4
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
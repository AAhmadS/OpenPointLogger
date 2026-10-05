import time

from trailmark.hotkey import HotkeyListener

print("probe ctrl+alt+P:", HotkeyListener.probe(["ctrl", "alt"], "P"))
print("label:", HotkeyListener(["ctrl", "alt"], "P", lambda: None).label)

state = {"n": 0}


def press():
    state["n"] += 1


h = HotkeyListener(["ctrl", "alt"], "P", press)
h.start()
time.sleep(1)
print("registered:", h._registered)
h.stop()
print("stopped ok")

# T11: a second, independent listener (distinct hotkey_id) must coexist with
# the first - default _id stays 0x4343, the clipboard hotkey uses 0x4344.
# Only construction + id + stop are asserted here; .start() is not, since
# another app may legitimately already hold Ctrl+Alt+V on the test machine.
default_h = HotkeyListener(["ctrl", "alt"], "P", lambda: None)
second_h = HotkeyListener(["ctrl", "alt"], "V", lambda: None, hotkey_id=0x4344)
assert default_h._id == 0x4343
assert second_h._id == 0x4344
second_h.stop()  # no-op: never started, must not raise
print("second listener id:", hex(second_h._id))
print("dual hotkey_id OK")

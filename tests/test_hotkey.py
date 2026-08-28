import time

from hotkey import HotkeyListener

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
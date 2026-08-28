import pathlib

from ui import MAIN_HTML, POPUP_HTML

pixel = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII="

out = pathlib.Path(__file__).resolve().parent / "_browser"
out.mkdir(exist_ok=True)

for name, html in (("popup.html", POPUP_HTML), ("main.html", MAIN_HTML)):
    (out / name).write_text(html.replace("__ICON__", pixel), encoding="utf-8")

print("wrote", out)
import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

import llm

captured = {}


class Handler(BaseHTTPRequestHandler):
    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        body = json.loads(self.rfile.read(length).decode("utf-8"))
        captured["path"] = self.path
        captured["auth"] = self.headers.get("Authorization")
        captured["model"] = body.get("model")
        captured["messages"] = body.get("messages")
        resp = {"choices": [{"message": {"content": "OK from mock"}}]}
        data = json.dumps(resp).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, *args):
        pass


server = HTTPServer(("127.0.0.1", 0), Handler)
thread = threading.Thread(target=server.serve_forever, daemon=True)
thread.start()
port = server.server_address[1]

cfg = {
    "enabled": True,
    "provider": "openrouter",
    "model": "deepseek/deepseek-v4-flash",
    "api_key": "test-key-123",
    "base_url": "http://127.0.0.1:%d/v1" % port,
}

res = llm.chat(cfg, "sys", "user hello")
assert res.get("content") == "OK from mock", res
assert captured["auth"] == "Bearer test-key-123"
assert captured["path"].endswith("/chat/completions")
assert captured["model"] == "deepseek/deepseek-v4-flash"

res = llm.polish_entry(cfg, "a  note  with   typpos")
assert res.get("content") == "OK from mock", res

cfg_bad = dict(cfg)
cfg_bad["enabled"] = False
res = llm.chat(cfg_bad, "sys", "user")
assert "disabled" in res.get("error", "").lower(), res

cfg_bad = dict(cfg)
cfg_bad["api_key"] = ""
res = llm.chat(cfg_bad, "sys", "user")
assert "api key" in res.get("error", "").lower(), res

server.shutdown()
print("llm BYOK client OK; mock saw model:", captured["model"], "| auth header ok")
print("draft_summary reachable:", callable(llm.draft_summary))
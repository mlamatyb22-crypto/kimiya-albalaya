#!/usr/bin/env python3
"""جسر ريموت الشاشة: يستقبل أوامر من صفحة الجوال ويرسلها للشاشة عبر ADB.

التشغيل:  python3 server.py --tv 192.168.1.25
بدون مكتبات خارجية، يحتاج فقط python3 و adb.
"""
import argparse
import json
import os
import re
import shlex
import subprocess
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

HERE = Path(__file__).resolve().parent

# اسم الزر -> رمز Android keyevent
KEYS = {
    "up": "KEYCODE_DPAD_UP", "down": "KEYCODE_DPAD_DOWN",
    "left": "KEYCODE_DPAD_LEFT", "right": "KEYCODE_DPAD_RIGHT",
    "ok": "KEYCODE_DPAD_CENTER", "back": "KEYCODE_BACK",
    "home": "KEYCODE_HOME", "menu": "KEYCODE_MENU",
    "vol_up": "KEYCODE_VOLUME_UP", "vol_down": "KEYCODE_VOLUME_DOWN",
    "mute": "KEYCODE_VOLUME_MUTE",
    "ch_up": "KEYCODE_CHANNEL_UP", "ch_down": "KEYCODE_CHANNEL_DOWN",
    "play_pause": "KEYCODE_MEDIA_PLAY_PAUSE",
    "rewind": "KEYCODE_MEDIA_REWIND", "forward": "KEYCODE_MEDIA_FAST_FORWARD",
    "power": "KEYCODE_POWER", "sleep": "KEYCODE_SLEEP", "wake": "KEYCODE_WAKEUP",
    "input": "KEYCODE_TV_INPUT", "settings": "KEYCODE_SETTINGS",
    "info": "KEYCODE_INFO",
}

# أوامر جاهزة (كلها ثابتة، ما تتأثر بمدخلات المستخدم)
ACTIONS = {
    "open_settings": "am start -a android.settings.SETTINGS",
    "open_wifi": "am start -a android.settings.WIFI_SETTINGS",
    "open_dev_options": "am start -a android.settings.APPLICATION_DEVELOPMENT_SETTINGS",
}

SAFE_TEXT = re.compile(r"[^A-Za-z0-9 ._@\-]")
SAFE_PKG = re.compile(r"^[A-Za-z][A-Za-z0-9_]*(\.[A-Za-z0-9_]+)+$")


class Adb:
    def __init__(self, adb_path, tv, port):
        self.adb, self.tv, self.port = adb_path, tv, port
        self.lock = threading.Lock()

    @property
    def target(self):
        return f"{self.tv}:{self.port}" if self.tv else None

    def _run(self, args, timeout=8):
        p = subprocess.run([self.adb, *args], capture_output=True, text=True, timeout=timeout)
        return p.returncode, (p.stdout + p.stderr).strip()

    def connect(self):
        if not self.tv:
            return False, "لم يُحدَّد عنوان الشاشة (IP)"
        _, out = self._run(["connect", self.target])
        ok = "connected" in out and "cannot" not in out and "failed" not in out
        return ok, out

    def connected(self):
        try:
            _, out = self._run(["devices"])
        except Exception:
            return False
        return any(l.startswith(self.target or "\0") and l.endswith("device")
                   for l in out.splitlines())

    def shell(self, command):
        with self.lock:
            if not self.connected():
                ok, out = self.connect()
                if not ok:
                    return False, out
            rc, out = self._run(["-s", self.target, "shell", command])
            return rc == 0, out


def load_apps():
    path = HERE / "apps.json"
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return []


def make_handler(adb, pin):
    apps = load_apps()
    app_pkgs = {a["package"] for a in apps}

    class H(BaseHTTPRequestHandler):
        def log_message(self, *a):
            pass

        def _send(self, code, body, ctype="application/json; charset=utf-8"):
            data = body if isinstance(body, bytes) else json.dumps(body, ensure_ascii=False).encode()
            self.send_response(code)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(data)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(data)

        def _authed(self):
            return not pin or self.headers.get("X-Pin") == pin

        def do_GET(self):
            path = urlparse(self.path).path
            if path in ("/", "/index.html"):
                return self._send(200, (HERE / "index.html").read_bytes(), "text/html; charset=utf-8")
            if path == "/api/apps":
                return self._send(200, {"apps": apps, "pin_required": bool(pin)})
            if path == "/api/status":
                if not self._authed():
                    return self._send(401, {"ok": False, "msg": "الرقم السري غير صحيح"})
                return self._send(200, {"ok": True, "connected": adb.connected(), "tv": adb.target})
            self._send(404, {"ok": False, "msg": "غير موجود"})

        def do_POST(self):
            if not self._authed():
                return self._send(401, {"ok": False, "msg": "الرقم السري غير صحيح"})
            try:
                n = int(self.headers.get("Content-Length") or 0)
                body = json.loads(self.rfile.read(min(n, 4096)) or b"{}")
            except Exception:
                return self._send(400, {"ok": False, "msg": "طلب غير صالح"})
            path = urlparse(self.path).path
            try:
                ok, msg = self.dispatch(path, body)
            except subprocess.TimeoutExpired:
                ok, msg = False, "انتهت المهلة، تأكد أن الشاشة شغالة ومتصلة بالشبكة"
            except FileNotFoundError:
                ok, msg = False, "أداة adb غير موجودة على هذا الجهاز"
            self._send(200 if ok else 502, {"ok": ok, "msg": msg})

        def dispatch(self, path, body):
            if path == "/api/connect":
                return adb.connect()
            if path == "/api/key":
                key = KEYS.get(body.get("key"))
                if not key:
                    return False, "زر غير معروف"
                return adb.shell(f"input keyevent {key}")
            if path == "/api/text":
                text = SAFE_TEXT.sub("", str(body.get("text", "")))[:200]
                if not text:
                    return False, "النص فاضي أو فيه رموز غير مدعومة (الإنجليزي والأرقام فقط)"
                return adb.shell("input text " + shlex.quote(text.replace(" ", "%s")))
            if path == "/api/url":
                url = str(body.get("url", "")).strip()
                u = urlparse(url)
                if u.scheme not in ("http", "https") or not u.netloc or len(url) > 1000:
                    return False, "الرابط لازم يبدأ بـ http أو https"
                return adb.shell("am start -a android.intent.action.VIEW -d " + shlex.quote(url))
            if path == "/api/app":
                pkg = str(body.get("package", ""))
                if pkg not in app_pkgs or not SAFE_PKG.match(pkg):
                    return False, "تطبيق غير مسجّل في apps.json"
                return adb.shell(f"monkey -p {pkg} -c android.intent.category.LAUNCHER 1")
            if path == "/api/action":
                cmd = ACTIONS.get(body.get("name"))
                if not cmd:
                    return False, "أمر غير معروف"
                return adb.shell(cmd)
            return False, "غير موجود"

    return H


def main():
    ap = argparse.ArgumentParser(description="ريموت الشاشة بالجوال عبر ADB")
    ap.add_argument("--tv", default=os.environ.get("TV_IP"), help="عنوان IP للشاشة")
    ap.add_argument("--adb-port", type=int, default=5555)
    ap.add_argument("--adb", default=os.environ.get("ADB", "adb"), help="مسار أداة adb")
    ap.add_argument("--port", type=int, default=8080, help="منفذ صفحة الريموت")
    ap.add_argument("--host", default="0.0.0.0")
    ap.add_argument("--pin", default=os.environ.get("REMOTE_PIN"), help="رقم سري اختياري")
    a = ap.parse_args()

    adb = Adb(a.adb, a.tv, a.adb_port)
    srv = ThreadingHTTPServer((a.host, a.port), make_handler(adb, a.pin))
    print(f"الريموت شغال: افتح من الجوال  http://<عنوان-هذا-الجهاز>:{a.port}")
    print(f"الشاشة: {adb.target or 'غير محددة'}")
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()

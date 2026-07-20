#!/usr/bin/env python3
from __future__ import annotations

import base64
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "rss-src"
OUT = ROOT / "rss"
FEEDS = ROOT / "scripts" / "feeds.json"
KEY = b"cgk2026rss"
JS_OUT = OUT / "x7f2a.js"
CSS_OUT = OUT / "k9m3.css"
DATA_OUT = OUT / "c.v1"


def encode_payload(text: str) -> str:
    raw = text.encode("utf-8")
    xored = bytes(raw[i] ^ KEY[i % len(KEY)] for i in range(len(raw)))
    return base64.b64encode(xored).decode("ascii")


def decode_payload(encoded: str) -> str:
    xored = base64.b64decode(encoded)
    raw = bytes(xored[i] ^ KEY[i % len(KEY)] for i in range(len(xored)))
    return raw.decode("utf-8")


def minify_css(text: str) -> str:
    text = re.sub(r"/\*.*?\*/", "", text, flags=re.S)
    text = re.sub(r"\s+", " ", text)
    return text.replace(" {", "{").replace("{ ", "{").replace(" }", "}").replace("; ", ";").strip()


def minify_js(text: str) -> str:
    text = re.sub(r"/\*.*?\*/", "", text, flags=re.S)
    text = re.sub(r"^\s*//.*$", "", text, flags=re.M)
    text = re.sub(r"\n\s+", "\n", text)
    text = re.sub(r"\s*\n\s*", "", text)
    text = re.sub(r"\s{2,}", " ", text)
    return text.strip()


def build() -> int:
    if not FEEDS.exists():
        print(f"Missing feeds file: {FEEDS}", file=sys.stderr)
        return 1
    if not (SRC / "app.js").exists() or not (SRC / "app.css").exists():
        print("Missing rss-src/app.js or rss-src/app.css", file=sys.stderr)
        return 1

    payload = FEEDS.read_text(encoding="utf-8")
    json.loads(payload)
    DATA_OUT.write_text(encode_payload(payload), encoding="utf-8")

    css = minify_css((SRC / "app.css").read_text(encoding="utf-8"))
    css += "\nbody{-webkit-user-select:none;user-select:none}input,textarea,.rss-link,.site-name{-webkit-user-select:text;user-select:text}"
    CSS_OUT.write_text(css, encoding="utf-8")

    js = (SRC / "app.js").read_text(encoding="utf-8")
    js = js.replace("const dataUrl = 'data.v1';", "const dataUrl=String.fromCharCode(99,46,118,49);")
    js = js.replace(
        "fetch(dataUrl)\n    .then(res => {\n      if (!res.ok) throw new Error('Veri dosyası bulunamadı');\n      return res.json();\n    })\n    .then(data => {",
        "fetch(dataUrl).then(r=>{if(!r.ok)throw new Error('x');return r.text()}).then(t=>{const k=atob(t),b=new Uint8Array(k.length),x=[99,103,107,50,48,50,54,114,115,115];for(let i=0;i<k.length;i++)b[i]=k.charCodeAt(i)^x[i%x.length];const data=JSON.parse(new TextDecoder().decode(b));",
    )
    guard = (
        "document.addEventListener('contextmenu',e=>e.preventDefault());"
        "document.addEventListener('keydown',e=>{"
        "if((e.ctrlKey||e.metaKey)&&['s','u','c','a'].includes(e.key.toLowerCase()))e.preventDefault();"
        "if(e.key==='F12'||(e.ctrlKey&&e.shiftKey&&['i','j','c'].includes(e.key.toLowerCase())))e.preventDefault();"
        "});"
    )
    JS_OUT.write_text(minify_js(guard + js), encoding="utf-8")

    print(f"Built {DATA_OUT.name}, {JS_OUT.name}, {CSS_OUT.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(build())

#!/usr/bin/env python3
"""
KDK Bundler – Inlines all CSS, JS, images and PDFs into self-contained HTML files.
Usage: python3 bundler.py [--watch]
"""

import base64
import mimetypes
import os
import re
import sys
import time

# Quell- → Ausgabe-Dateien
TARGETS = [
    ("src.html",        "index.html"),
    ("impressum_src.html", "impressum.html"),
]
BASE = os.path.dirname(os.path.abspath(__file__))

# Ausgabedateien aus der Dateiüberwachung ausschließen
OUT_FILES = {t[1] for t in TARGETS}


_MIME_OVERRIDES = {
    ".ttf":   "font/ttf",
    ".woff":  "font/woff",
    ".woff2": "font/woff2",
    ".otf":   "font/otf",
    ".ico":   "image/x-icon",
}

def encode_file(path: str) -> str:
    ext = os.path.splitext(path)[1].lower()
    mime = _MIME_OVERRIDES.get(ext) or mimetypes.guess_type(path)[0]
    if mime is None:
        mime = "application/octet-stream"
    with open(path, "rb") as f:
        data = base64.b64encode(f.read()).decode("ascii")
    return f"data:{mime};base64,{data}"


def resolve(src_attr: str) -> str | None:
    if src_attr.startswith("data:") or src_attr.startswith("http"):
        return None
    return os.path.join(BASE, src_attr)


def minify_css(css: str) -> str:
    css = re.sub(r'/\*.*?\*/', '', css, flags=re.DOTALL)  # Kommentare
    css = re.sub(r'\s+', ' ', css)                         # Whitespace
    css = re.sub(r'\s*([{}:;,>+~])\s*', r'\1', css)       # um Sonderzeichen
    css = re.sub(r';+}', '}', css)                         # letztes Semikolon
    return css.strip()


def minify_html(html: str) -> str:
    html = re.sub(r'<!--(?!(\[if|\s*#)).*?-->', '', html, flags=re.DOTALL)  # Kommentare
    html = re.sub(r'>\s+<', '><', html)                    # Whitespace zwischen Tags
    html = re.sub(r'\s{2,}', ' ', html)                    # doppelte Leerzeichen
    return html.strip()


def bundle_file(src: str, out: str) -> None:
    with open(os.path.join(BASE, src), encoding="utf-8") as f:
        html = f.read()

    # 1. Inline <link rel="stylesheet">
    def inline_css(m):
        path = resolve(m.group(1))
        if path is None or not os.path.exists(path):
            return m.group(0)
        with open(path, encoding="utf-8") as f:
            css = f.read()
        def inline_url(um):
            url = um.group(1).strip("'\"")
            abs_url = resolve(os.path.join(os.path.dirname(path), url))
            if abs_url and os.path.exists(abs_url):
                return f'url("{encode_file(abs_url)}")'
            return um.group(0)
        css = re.sub(r'url\(([^)]+)\)', inline_url, css)
        return f"<style>{minify_css(css)}</style>"

    html = re.sub(
        r'<link[^>]+rel=["\']stylesheet["\'][^>]+href=["\']([^"\']+)["\'][^>]*/?>',
        inline_css, html)
    html = re.sub(
        r'<link[^>]+href=["\']([^"\']+)["\'][^>]+rel=["\']stylesheet["\'][^>]*/?>',
        inline_css, html)

    # 2. Inline <script src="...">
    def inline_js(m):
        path = resolve(m.group(1))
        if path is None or not os.path.exists(path):
            return m.group(0)
        with open(path, encoding="utf-8") as f:
            js = f.read()
        return f"<script>\n{js}\n</script>"

    html = re.sub(r'<script\s+src=["\']([^"\']+)["\']([^>]*)></script>', inline_js, html)

    # 3. Inline <img src="...">
    def inline_img(m):
        prefix, src, suffix = m.group(1), m.group(2), m.group(3)
        path = resolve(src)
        if path is None or not os.path.exists(path):
            return m.group(0)
        return f'{prefix}{encode_file(path)}{suffix}'

    html = re.sub(r'(<img[^>]+src=["\'])([^"\']+)(["\'])', inline_img, html)

    # 4a. Inline <link rel="icon"> favicon
    def inline_favicon(m):
        prefix, href, suffix = m.group(1), m.group(2), m.group(3)
        path = resolve(href)
        if path and os.path.exists(path):
            return f'{prefix}{encode_file(path)}{suffix}'
        return m.group(0)

    html = re.sub(r'(<link[^>]+rel=["\']icon["\'][^>]+href=["\'])([^"\']+)(["\'])', inline_favicon, html)
    html = re.sub(r'(<link[^>]+href=["\'])([^"\']+)(["\'][^>]+rel=["\'](?:icon|shortcut icon)["\'])', inline_favicon, html)

    # 4b. iframe – PDF-Previews werden NICHT gebundelt (bleiben als externe Datei)

    # 5. PDFs bleiben als externe Dateien (bessere Performance)

    html = minify_html(html)

    out_path = os.path.join(BASE, out)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html)

    size_kb = os.path.getsize(out_path) / 1024
    print(f"  Bundled → {out}  ({size_kb:.0f} KB)")


def bundle_all() -> None:
    for src, out in TARGETS:
        src_path = os.path.join(BASE, src)
        if os.path.exists(src_path):
            bundle_file(src, out)
        else:
            print(f"  Übersprungen: {src} (nicht gefunden)")


def watched_files() -> dict[str, float]:
    result = {}
    for root, _, files in os.walk(BASE):
        for name in files:
            if name in OUT_FILES or name == "bundler.py":
                continue
            ext = os.path.splitext(name)[1].lower()
            if ext in (".html", ".css", ".js", ".png", ".jpg", ".jpeg",
                       ".gif", ".svg", ".webp", ".pdf",
                       ".ttf", ".woff", ".woff2", ".otf", ".ico"):
                p = os.path.join(root, name)
                result[p] = os.path.getmtime(p)
    return result


if __name__ == "__main__":
    watch = "--watch" in sys.argv

    print("KDK Bundler")
    print("=" * 42)
    bundle_all()

    if watch:
        print("\nWatch mode aktiv – Strg+C zum Beenden\n")
        snapshot = watched_files()
        try:
            while True:
                time.sleep(1)
                current = watched_files()
                changed = [p for p, t in current.items()
                           if snapshot.get(p) != t or p not in snapshot]
                if changed:
                    for p in changed:
                        print(f"  Geändert: {os.path.relpath(p, BASE)}")
                    bundle_all()
                    snapshot = current
        except KeyboardInterrupt:
            print("\nBeendet.")

#!/usr/bin/env python3
"""HTTP server that renders Geometry Dash icons based on query parameters.

SPDX-License-Identifier: AGPL-3.0-or-later
"""

import io
import json
import mimetypes
import os
import sys
import urllib.parse
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path

# ── Use the local (forked) gdicons ────────────────────────────────────────────
# We ship a modified copy of gdicons in the repository so we can fix the
# module-level Windows-only default path.  See README.md for details.
sys.path.insert(0, str(Path(__file__).resolve().parent))

from gdicons import set_resources_path, render_icon

# ── Locate Resources folder ───────────────────────────────────────────────────

def _find_resources():
    """Search order: GDICONS_RESOURCES env var → script dir → CWD."""
    candidates = []
    env = os.environ.get("GDICONS_RESOURCES")
    if env:
        candidates.append(Path(env))
    candidates.append(Path(sys.path[0]) / "Resources")
    candidates.append(Path.cwd() / "Resources")

    for path in candidates:
        resolved = path.resolve()
        if resolved.is_dir() and (resolved / "icons").is_dir():
            return resolved

    raise RuntimeError(
        "Cannot find Geometry Dash Resources folder. "
        "Set the GDICONS_RESOURCES environment variable or place a "
        "Resources/ folder next to the script."
    )

_RESOURCES_PATH = _find_resources()
set_resources_path(str(_RESOURCES_PATH))

# ── Valid values ──────────────────────────────────────────────────────────────

VALID_GAMEMODES = {
    "cube", "ship", "ball", "ufo",
    "wave", "robot", "spider", "swing", "jetpack",
}

VALID_QUALITIES = {"low", "normal", "hd", "uhd"}


# ── Helper: parse a colour argument ───────────────────────────────────────────

def parse_color(raw, allow_true=False):
    """Return a colour value suitable for render_icon().

    * ``false`` / ``False`` / ``"false"`` → ``False`` (disable glow)
    * ``true`` / ``True`` / ``"true"``   → ``True``  (use secondary) — only when *allow_true* is set
    * integer string (``"0"`` … ``"123"``) → int (GD colour ID)
    * hex string (``"#rrggbb"``) → kept as-is
    * named colour (``"red"``) → kept as-is
    """
    if isinstance(raw, bool):
        return raw
    lower = raw.strip().lower()
    if lower in ("false", "none", "null", ""):
        return False
    if allow_true and lower in ("true",):
        return True
    # GD colour ID (integer)
    if lower.isdigit() or (lower.startswith("-") and lower[1:].isdigit()):
        return int(lower)
    # Already a valid colour string
    return raw


# ── Request handler ───────────────────────────────────────────────────────────

class IconHandler(BaseHTTPRequestHandler):

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)

        # ── Health / info endpoint ────────────────────────────────────────
        if parsed.path == "/":
            self._send_json(200, {
                "status": "ok",
                "resources": str(_RESOURCES_PATH),
                "endpoints": {
                    "GET /": "this info",
                    "GET /icon": "render an icon (see query parameters)",
                    "GET /random": "redirect to a random icon",
                },
            })
            return

        # ── Random icon redirect ──────────────────────────────────────────
        if parsed.path == "/random":
            params = _random_example_params()
            location = "/icon?" + urllib.parse.urlencode(params)
            self.send_response(302)
            self.send_header("Location", location)
            self.end_headers()
            return

        # ── Serve static files ────────────────────────────────────────────
        if parsed.path == "/test.html":
            script_dir = Path(__file__).resolve().parent
            file_path = script_dir / "test.html"
            if file_path.is_file():
                content = file_path.read_bytes()
                mime_type, _ = mimetypes.guess_type(str(file_path))
                self.send_response(200)
                self.send_header("Content-Type", mime_type or "text/html")
                self.send_header("Content-Length", str(len(content)))
                self.end_headers()
                self.wfile.write(content)
                return

        if parsed.path != "/icon":
            self._send_json(404, {"error": "Not found", "path": parsed.path})
            return

        # ── Parse query parameters ────────────────────────────────────────
        params = urllib.parse.parse_qs(parsed.query, keep_blank_values=True)

        def get_param(name, default=None):
            values = params.get(name, [])
            if not values:
                return default
            return values[-1]  # last value wins

        gamemode = get_param("gamemode")
        raw_id   = get_param("id")
        primary   = get_param("primary")
        secondary = get_param("secondary")
        glow      = get_param("glow")       # default handled below
        quality   = get_param("quality", "uhd")

        # ── Validate ──────────────────────────────────────────────────────
        errors = []

        if not gamemode:
            errors.append("'gamemode' is required")
        elif gamemode not in VALID_GAMEMODES:
            errors.append(
                f"Invalid gamemode '{gamemode}'. "
                f"Must be one of: {', '.join(sorted(VALID_GAMEMODES))}"
            )

        icon_id = None
        if raw_id is None:
            errors.append("'id' is required")
        else:
            try:
                icon_id = int(raw_id)
            except ValueError:
                errors.append(f"'id' must be an integer, got '{raw_id}'")

        if not primary:
            errors.append("'primary' is required")

        if not secondary:
            errors.append("'secondary' is required")

        if quality and quality not in VALID_QUALITIES:
            errors.append(
                f"Invalid quality '{quality}'. "
                f"Must be one of: {', '.join(sorted(VALID_QUALITIES))}"
            )

        if errors:
            self._send_json(400, {"error": "Validation failed", "details": errors})
            return

        # ── Render ────────────────────────────────────────────────────────
        try:
            img = render_icon(
                gamemode=gamemode,
                id=icon_id,
                primary=parse_color(primary),
                secondary=parse_color(secondary),
                glow=parse_color(glow, allow_true=True) if glow is not None else False,
                quality=quality,
            )
        except Exception as exc:
            self._send_json(500, {"error": "Rendering failed", "details": str(exc)})
            return

        # ── Return PNG ────────────────────────────────────────────────────
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        png_data = buf.getvalue()

        self.send_response(200)
        self.send_header("Content-Type", "image/png")
        self.send_header("Content-Length", str(len(png_data)))
        self.send_header("Cache-Control", "public, max-age=3600")
        self.end_headers()
        self.wfile.write(png_data)

    # ── Helpers ───────────────────────────────────────────────────────────

    def _send_json(self, status, data):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format, *args):
        """Prepend a timestamp to each log line."""
        import datetime
        ts = datetime.datetime.now().strftime("%H:%M:%S")
        sys.stderr.write(f"[{ts}] {args[0]} {args[1]} {args[2]}\n")


# ── CLI entry point ───────────────────────────────────────────────────────────

def _random_example_params():
    """Return a dict of random valid params for the startup hint."""
    import random

    gamemodes = list(VALID_GAMEMODES)
    gamemode = random.choice(gamemodes)

    # Max icon ID per gamemode (from available spritesheets)
    _MAX_IDS = {
        "cube": 485, "ship": 169, "ball": 118, "ufo": 149,
        "wave": 96, "robot": 68, "spider": 69, "swing": 43, "jetpack": 8,
    }
    icon_id = random.randint(1, _MAX_IDS[gamemode])

    color_id_1 = random.randint(0, 106)
    color_id_2 = random.randint(0, 106)
    # ensure different
    while color_id_2 == color_id_1:
        color_id_2 = random.randint(0, 106)

    # glow: 80% random colour, 20% disabled
    if random.random() < 0.8:
        glow_id = random.randint(0, 106)
        glow = str(glow_id)
    else:
        glow = "false"

    return {
        "gamemode": gamemode,
        "id": icon_id,
        "primary": str(color_id_1),
        "secondary": str(color_id_2),
        "glow": glow,
    }


def main():
    import argparse

    parser = argparse.ArgumentParser(description="GD Icon Render HTTP Server")
    parser.add_argument(
        "--host", default="127.0.0.1",
        help="Bind address (default: 127.0.0.1)",
    )
    parser.add_argument(
        "--port", type=int, default=8080,
        help="Port number (default: 8080)",
    )
    args = parser.parse_args()

    server = HTTPServer((args.host, args.port), IconHandler)

    # Build a random example URL
    import urllib.parse
    ex = _random_example_params()
    example_url = (
        f"http://{args.host}:{args.port}/icon?"
        + urllib.parse.urlencode(ex)
    )

    print(f"🎨 GD Icon Render server listening on http://{args.host}:{args.port}")
    print(f"   Resources: {_RESOURCES_PATH}")
    print(f"   Try:       curl '{example_url}'")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down…")
        server.server_close()


if __name__ == "__main__":
    main()

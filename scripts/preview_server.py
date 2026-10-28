"""Serve the icon gallery on localhost with automatic asset change detection."""

import argparse
import hashlib
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import threading
import time
from urllib.parse import unquote, urlsplit
import webbrowser


ROOT = Path(__file__).resolve().parents[1]


class PreviewState:
    def __init__(self, root):
        self.root = root
        self.lock = threading.Lock()
        self.checked = 0
        self.snapshot = None

    def read(self):
        with self.lock:
            if self.snapshot and time.monotonic() - self.checked < 0.5:
                return self.snapshot
            # A partially saved manifest must not replace the last usable snapshot.
            manifest = json.loads((self.root / 'manifest.json').read_text(encoding='utf-8'))
            icons = sorted(manifest['icons'], key=lambda e: (e['category'], Path(e['source']).name))
            files = [self.root / name for name in ('manifest.json', 'gallery.html')]
            for folder in ('source', '24', '30', '36', '48', 'preview'):
                files.extend(p for p in (self.root / folder).rglob('*')
                             if p.suffix.lower() in {'.png', '.svg', '.js', '.css'} and p.is_file())
            stats = []
            for path in sorted(files):
                stat = path.stat()
                stats.append((path.relative_to(self.root).as_posix(), stat.st_mtime_ns, stat.st_size))
            revision = hashlib.sha256(json.dumps(stats).encode()).hexdigest()[:20]
            ui = [(name, stamp, size) for name, stamp, size in stats
                  if name == 'gallery.html' or name.startswith('preview/')]
            ui_revision = hashlib.sha256(json.dumps(ui).encode()).hexdigest()[:20]
            self.snapshot = {'revision': revision, 'uiRevision': ui_revision, 'icons': icons}
            self.checked = time.monotonic()
            return self.snapshot


class PreviewHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(args[2].root), **kwargs)

    def end_headers(self):
        self.send_header('Cache-Control', 'no-store')
        self.send_header('X-Content-Type-Options', 'nosniff')
        super().end_headers()

    def do_GET(self):
        if urlsplit(self.path).path == '/':
            self.path = '/gallery.html'
        if urlsplit(self.path).path == '/api/state':
            try:
                state = self.server.state.read()
            except (OSError, ValueError, KeyError, TypeError):
                self.send_error(HTTPStatus.SERVICE_UNAVAILABLE, 'Files are being saved; retry shortly')
                return
            etag = '"' + state['revision'] + '"'
            if self.headers.get('If-None-Match') == etag:
                self.send_response(HTTPStatus.NOT_MODIFIED)
                self.send_header('ETag', etag)
                self.end_headers()
                return
            payload = json.dumps(state, ensure_ascii=False).encode('utf-8')
            self.send_response(HTTPStatus.OK)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.send_header('Content-Length', str(len(payload)))
            self.send_header('ETag', etag)
            self.end_headers()
            self.wfile.write(payload)
            return
        if not self.allowed_path():
            self.send_error(HTTPStatus.NOT_FOUND)
            return
        super().do_GET()

    def do_HEAD(self):
        if urlsplit(self.path).path == '/':
            self.path = '/gallery.html'
        if not self.allowed_path():
            self.send_error(HTTPStatus.NOT_FOUND)
            return
        super().do_HEAD()

    def allowed_path(self):
        requested = unquote(urlsplit(self.path).path).lstrip('/') or 'gallery.html'
        path = (self.server.root / requested).resolve()
        if not path.is_relative_to(self.server.root) or not path.is_file():
            return False
        relative = path.relative_to(self.server.root)
        return (relative.as_posix() == 'gallery.html'
                or relative.parts[0] in {'source', '24', '30', '36', '48'}
                and path.suffix.lower() in {'.png', '.svg'}
                or relative.parts[0] == 'preview' and path.suffix.lower() in {'.css', '.js'})

    def log_message(self, format, *args):
        # Keep the launcher quiet during polling and lazy image loading.
        if args and str(args[1] if len(args) > 1 else '') not in {'200', '304'}:
            super().log_message(format, *args)


def create_server(root=ROOT, port=8765):
    server = ThreadingHTTPServer(('127.0.0.1', port), PreviewHandler)
    server.root = Path(root).resolve()
    server.state = PreviewState(server.root)
    return server


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port', type=int, default=8765)
    parser.add_argument('--no-browser', action='store_true')
    args = parser.parse_args()
    try:
        server = create_server(port=args.port)
    except OSError as error:
        parser.exit(1, f'Cannot start preview: {error}. Try --port 8766.\n')
    url = f'http://127.0.0.1:{server.server_port}/gallery.html'
    print(f'Icon preview: {url}\nPress Ctrl+C to stop.', flush=True)
    if not args.no_browser:
        webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == '__main__':
    main()

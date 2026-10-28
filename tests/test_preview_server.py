"""Exercise live asset updates and the local preview's HTTP boundary."""

from http.client import HTTPConnection
import json
from pathlib import Path
import tempfile
import threading
import unittest

from scripts.preview_server import create_server


class PreviewServerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        (self.root / 'manifest.json').write_text(json.dumps({'icons': []}), encoding='utf-8')
        (self.root / 'gallery.html').write_text('<h1>Preview</h1>', encoding='utf-8')
        for name in ('source', '24', '30', '36', '48', 'preview', '.git'):
            (self.root / name).mkdir()
        (self.root / '.git/config').write_text('private repository config', encoding='utf-8')
        self.server = create_server(self.root, 0)
        self.worker = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.worker.start()
        self.client = HTTPConnection('127.0.0.1', self.server.server_port, timeout=3)

    def tearDown(self):
        self.client.close()
        self.server.shutdown()
        self.server.server_close()
        self.worker.join(timeout=3)
        self.temp.cleanup()

    def request(self, path, headers=None, method='GET'):
        self.client.request(method, path, headers=headers or {})
        response = self.client.getresponse()
        return response.status, dict(response.getheaders()), response.read()

    def test_root_serves_gallery_and_private_or_directory_paths_are_not_served(self):
        status, headers, payload = self.request('/')
        self.assertEqual(status, 200)
        self.assertIn(b'<h1>Preview</h1>', payload)
        self.assertEqual(headers['Cache-Control'], 'no-store')
        for path in ('/.git/config', '/manifest.json', '/scripts/preview_server.py',
                     '/source/', '/%2e%2e/secret.txt', '/source/%2e%2e/.git/config'):
            with self.subTest(path=path):
                self.assertEqual(self.request(path)[0], 404)
                self.assertEqual(self.request(path, method='HEAD')[0], 404)

    def test_etag_changes_for_new_edited_and_deleted_assets_and_manifest(self):
        status, headers, body = self.request('/api/state')
        self.assertEqual(status, 200)
        previous = json.loads(body)
        self.assertEqual(self.request('/api/state', {'If-None-Match': headers['ETag']})[0], 304)
        image = self.root / '24/test.png'
        for operation in (lambda: image.write_bytes(b'first'),
                          lambda: image.write_bytes(b'updated-image'), image.unlink):
            operation()
            self.server.state.checked = 0
            next_state = json.loads(self.request('/api/state')[2])
            self.assertNotEqual(previous['revision'], next_state['revision'])
            self.assertEqual(previous['uiRevision'], next_state['uiRevision'])
            previous = next_state
        (self.root / 'manifest.json').write_text(json.dumps({'icons': [
            {'category': 'tools', 'source': 'source/tools/new.png', 'name': 'new'}]}), encoding='utf-8')
        self.server.state.checked = 0
        next_state = json.loads(self.request('/api/state')[2])
        self.assertEqual(next_state['icons'][0]['name'], 'new')
        self.assertNotEqual(previous['revision'], next_state['revision'])

    def test_partial_manifest_save_recovers_on_next_request(self):
        self.request('/api/state')
        (self.root / 'manifest.json').write_text('{', encoding='utf-8')
        self.server.state.checked = 0
        self.assertEqual(self.request('/api/state')[0], 503)
        (self.root / 'manifest.json').write_text('{"icons": []}', encoding='utf-8')
        self.assertEqual(self.request('/api/state')[0], 200)

    def test_ui_edit_has_its_own_reload_revision(self):
        previous = json.loads(self.request('/api/state')[2])
        (self.root / 'preview/preview.css').write_text('body {color: red}', encoding='utf-8')
        self.server.state.checked = 0
        next_state = json.loads(self.request('/api/state')[2])
        self.assertNotEqual(previous['uiRevision'], next_state['uiRevision'])


if __name__ == '__main__':
    unittest.main()

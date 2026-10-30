"""Guard the Leaflet CDN Subresource Integrity values.

A wrong integrity hash makes the browser block the file silently. A blocked
leaflet.css leaves every map pane `position: static`, so tiles and pins collapse
and the map can no longer be panned (v1.2.1 shipped this way).
"""
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# Published on https://leafletjs.com/download.html for Leaflet 1.9.4 and
# verified against the npm tarball (unpkg serves the same bytes).
LEAFLET_SRI = {
    'https://unpkg.com/leaflet@1.9.4/dist/leaflet.css':
        'sha256-p4NxAoJBhIIN+hmNHrzRCf9tD/miZyoHS5obTRR9BMY=',
    'https://unpkg.com/leaflet@1.9.4/dist/leaflet.js':
        'sha256-20nQCchB9co0qIjJZRGuk2/Z9VM+kNiyxNV1lvTlZBo=',
}
TAG = re.compile(r'<(?:link|script)\b[^>]*?(?:href|src)="(https://unpkg\.com/leaflet@[^"]+)"[^>]*>')
INTEGRITY = re.compile(r'\bintegrity="([^"]+)"')


class LeafletIntegrityTests(unittest.TestCase):
    def check(self, path: Path):
        html = path.read_text('utf-8')
        found = {}
        for match in TAG.finditer(html):
            integrity = INTEGRITY.search(match.group(0))
            self.assertIsNotNone(integrity, f'{path.name}: {match.group(1)} lacks integrity')
            self.assertIn('crossorigin', match.group(0), f'{path.name}: SRI needs crossorigin')
            found[match.group(1)] = integrity.group(1)
        self.assertEqual(found, LEAFLET_SRI, f'{path.name}: Leaflet SRI mismatch')

    def test_template_uses_published_hashes(self):
        self.check(ROOT / 'scripts/index.template.html')

    def test_generated_html_uses_published_hashes(self):
        self.check(ROOT / 'index.html')


if __name__ == '__main__':
    unittest.main()

import json
import tempfile
import unittest
from pathlib import Path

from scripts.build_embedded import (
    COMPACT_SCHEMA, FIELDS, FALLBACK_LIMIT, build_outputs,
    compact_catalog, offline_fallback
)

ROOT = Path(__file__).resolve().parents[1]


class CompactCatalogTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.spots = json.loads((ROOT / 'data/spots.json').read_text('utf-8'))
        cls.live = json.loads((ROOT / 'data/live.json').read_text('utf-8'))

    def test_every_spot_survives_compaction(self):
        lite = compact_catalog(self.spots)
        self.assertEqual(lite['schemaVersion'], COMPACT_SCHEMA)
        self.assertEqual(lite['fields'], FIELDS)
        self.assertEqual(len(lite['rows']), len(self.spots))
        self.assertEqual([r[0] for r in lite['rows']], [s['id'] for s in self.spots])
        for row, source in zip(lite['rows'], self.spots):
            self.assertEqual(row[1], source['name'])
            self.assertEqual(row[2], source['prefecture'])
            self.assertLessEqual(abs(row[3] - source['lat']), 0.000001)
            self.assertLessEqual(abs(row[4] - source['lon']), 0.000001)
            self.assertEqual(row[5], (source.get('camera') or {}).get('url', ''))
            self.assertEqual(row[7], int(bool(source.get('candidate'))))
        compact_size = len(json.dumps(lite, ensure_ascii=False, separators=(',', ':')).encode('utf-8'))
        full_size = (ROOT / 'data/spots.json').stat().st_size
        # Lower bound keeps changes honest if source schema expands in future.
        self.assertLess(compact_size, full_size * 0.45)

    def test_offline_fallback_preserves_camera_and_reports(self):
        fallback = offline_fallback(self.spots, self.live)
        self.assertLessEqual(len(fallback), FALLBACK_LIMIT)
        ids = {spot['id'] for spot in fallback}
        self.assertEqual(len(ids), len(fallback))
        self.assertTrue({s['id'] for s in self.spots if s.get('camera')}.issubset(ids))
        reported = {s['id'] for s in self.spots if s['id'] in self.live['reports']
                    and not s.get('candidate')}
        self.assertTrue(reported.issubset(ids))

    def test_generated_assets_load_and_cover_every_prefecture(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / 'scripts').mkdir()
            (root / 'data').mkdir()
            for relative in ('data/spots.json', 'data/live.json', 'scripts/index.template.html'):
                src = ROOT / relative
                dst = root / relative
                dst.write_bytes(src.read_bytes())
            metrics = build_outputs(root)
            self.assertEqual(metrics['spots'], len(self.spots))
            self.assertLess(metrics['compact_bytes'], metrics['source_bytes'] * .45)
            self.assertLess(metrics['html_bytes'], 38000)
            lite = json.loads((root / 'data/spots-lite.json').read_text('utf-8'))
            self.assertEqual(len(lite['rows']), len(self.spots))
            ids = []
            for path in (root / 'data/prefectures').glob('*.json'):
                ids.extend(s['id'] for s in json.loads(path.read_text('utf-8')))
            self.assertEqual(set(ids), {s['id'] for s in self.spots})
            self.assertEqual(len(ids), len(set(ids)))
            html = (root / 'index.html').read_text('utf-8')
            self.assertIn('id="bootstrap-data"', html)
            self.assertIn('"bounds":', html)
            self.assertNotIn('__EMBEDDED_DATA__', html)


if __name__ == '__main__':
    unittest.main()

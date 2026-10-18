import json
import unittest
from pathlib import Path
from datetime import date
from urllib.parse import urlsplit
ROOT=Path(__file__).resolve().parents[1]
VALID={'full','peak','starting','green','past','unknown'}

class FrontendMobileTests(unittest.TestCase):
    def test_lightweight_offline_bootstrap(self):
        builder=(ROOT/'scripts/build_embedded.py').read_text('utf-8')
        self.assertIn('if not spot.get("candidate")',builder)
        # The external static JSON must remain the source for full nationwide coverage.
        frontend=(ROOT/'assets/app.js').read_text('utf-8')
        self.assertIn("fetch('data/spots-lite.json'",frontend)

    def test_mobile_camera_and_search_controls(self):
        script=(ROOT/'assets/app.js').read_text('utf-8')
        template=(ROOT/'scripts/index.template.html').read_text('utf-8')
        styles=(ROOT/'assets/app.css').read_text('utf-8')
        self.assertIn("spot.camera?'📹'",script)
        self.assertIn("if(spot.camera)cameraOpen(spot)",script)
        self.assertIn('id="mobile-search"',template)
        self.assertIn('id="mobile-cameras"',template)
        self.assertIn('min-height:44px',styles)
        self.assertIn("state.spotsLoadedAt",script)
        self.assertIn("function decodeCatalog(",script)
        self.assertIn("function loadSpotDetails(",script)
        self.assertIn("state.detailCache.set(",script)
        self.assertIn("tileSize:state.lowData?512:256",script)
        self.assertIn("zoomOffset:state.lowData?-1:0",script)
        self.assertIn('id="map-quality"',template)
        self.assertNotIn("fonts.googleapis.com",template)

class SpotsIntegrity(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.spots=json.loads((ROOT/'data/spots.json').read_text('utf-8'))
        cls.seeds=json.loads((ROOT/'data/seed-observations.json').read_text('utf-8'))

    def test_enriched_sources_are_attributed(self):
        imported=[s for s in self.spots if s.get('candidate')]
        for spot in imported:
            with self.subTest(spot=spot['id']):
                self.assertTrue(spot['id'].startswith('wiki-'))
                self.assertEqual(spot['sourceName'],'Wikipedia / Wikidata（観光地位置情報）')
                self.assertEqual(urlsplit(spot['sourceUrl']).hostname,'ja.wikipedia.org')
                self.assertNotIn(spot['id'],self.seeds)

    def test_spots_unique_and_valid(self):
        self.assertGreaterEqual(len(self.spots),157)
        seen=set()
        for s in self.spots:
            with self.subTest(spot=s.get('id')):
                self.assertNotIn(s['id'],seen)
                seen.add(s['id'])
                self.assertTrue(s['name'] and s['prefecture'])
                self.assertTrue(24.0 < s['lat'] < 46.0)
                self.assertTrue(122.0 < s['lon'] < 148.0)
                if c:=s.get('camera'):
                    self.assertEqual(urlsplit(c['url']).scheme,'https')
                    self.assertTrue(urlsplit(c['url']).hostname)

    def test_every_prefecture_is_covered(self):
        prefectures=set('北海道 青森 岩手 宮城 秋田 山形 福島 茨城 栃木 群馬 埼玉 千葉 東京 神奈川 新潟 富山 石川 福井 山梨 長野 岐阜 静岡 愛知 三重 滋賀 京都 大阪 兵庫 奈良 和歌山 鳥取 島根 岡山 広島 山口 徳島 香川 愛媛 高知 福岡 佐賀 長崎 熊本 大分 宮崎 鹿児島 沖縄'.split())
        covered={s['prefecture'] for s in self.spots}
        self.assertEqual(covered,prefectures)

    def test_observations_link_existing_spots(self):
        ids={s['id'] for s in self.spots}
        for spot_id,r in self.seeds.items():
            with self.subTest(spot=spot_id):
                self.assertIn(spot_id,ids)
                self.assertIn(r['status'],VALID)
                date.fromisoformat(r['observedAt'])
                self.assertEqual(urlsplit(r['sourceUrl']).scheme,'https')

if __name__=='__main__':unittest.main()

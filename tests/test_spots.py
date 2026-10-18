import json
import unittest
from pathlib import Path
from datetime import date
from urllib.parse import urlsplit
ROOT=Path(__file__).resolve().parents[1]
VALID={'full','peak','starting','green','past','unknown'}

class SpotsIntegrity(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.spots=json.loads((ROOT/'data/spots.json').read_text('utf-8'))
        cls.seeds=json.loads((ROOT/'data/seed-observations.json').read_text('utf-8'))

    def test_spots_unique_and_valid(self):
        self.assertGreater(len(self.spots),20)
        seen=set()
        for s in self.spots:
            with self.subTest(spot=s.get('id')):
                self.assertNotIn(s['id'],seen)
                seen.add(s['id'])
                self.assertTrue(s['name'] and s['prefecture'])
                self.assertTrue(32.0 < s['lat'] < 40.0)
                self.assertTrue(136.0 < s['lon'] < 142.0)
                if c:=s.get('camera'):
                    self.assertEqual(urlsplit(c['url']).scheme,'https')
                    self.assertTrue(urlsplit(c['url']).hostname)

    def test_observations_link_existing_spots(self):
        ids={s['id'] for s in self.spots}
        for spot_id,r in self.seeds.items():
            with self.subTest(spot=spot_id):
                self.assertIn(spot_id,ids)
                self.assertIn(r['status'],VALID)
                date.fromisoformat(r['observedAt'])
                self.assertEqual(urlsplit(r['sourceUrl']).scheme,'https')

if __name__=='__main__':unittest.main()

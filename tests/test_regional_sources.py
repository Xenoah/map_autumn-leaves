"""Parsers for regional official pages and JMA phenology tables.

Fixtures mirror the published wording seen on each page (2026-10-31); the
parsers work on readable text, not on a site's HTML structure.
"""
import datetime as dt
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import update_data as ud  # noqa: E402
from bs4 import BeautifulSoup  # noqa: E402

TODAY = dt.date(2026, 10, 31)
IWATE = ud.OFFICIAL_SOURCES[0]
FUKUOKA = ud.OFFICIAL_SOURCES[1]


def spot(id_, name, pref):
    return {'id': id_, 'name': name, 'prefecture': pref}


class StageWordTests(unittest.TestCase):
    def test_stage_vocabulary(self):
        cases = {'まだ青葉': 'green', '黒門周辺は青葉': 'green', '色付き始め': 'starting',
                 '大楓の上の方が色づき始め': 'starting', '見頃間近': 'starting', '見頃': 'peak',
                 '見ごろ': 'peak', '最盛期': 'full', '終盤': 'past', '見ごろ終了': 'past',
                 '見ごろ終盤、イチョウ見ごろ': 'past', '落葉': 'past', 'ー': None, '': None}
        for text, expected in cases.items():
            with self.subTest(text=text):
                self.assertEqual(ud.stage_of(text), expected)

    def test_aliases_skip_short_and_municipal_names(self):
        self.assertEqual(ud.spot_aliases(spot('a', '平泉・中尊寺', '岩手')), ['中尊寺'])
        self.assertIn('姿見の池', ud.spot_aliases(spot('b', '大雪山・旭岳（姿見の池）', '北海道')))
        self.assertEqual(ud.spot_aliases(spot('c', '東公園 (福岡市)', '福岡')), ['東公園'])
        self.assertEqual(ud.spot_aliases(spot('d', '中津川 (岩手県)', '岩手')), ['中津川'])
        pattern = ud.alias_pattern('八幡平')
        self.assertIsNone(pattern.search('八幡平市 松川渓谷'))
        self.assertIsNotNone(pattern.search('八幡平市 八幡平 終盤'))


class IwateTests(unittest.TestCase):
    spots = [spot('iwate-hachimantai', '八幡平・見返峠', '岩手'),
             spot('iwate-chusonji', '平泉・中尊寺', '岩手'),
             spot('wiki-chusonji', '中尊寺', '岩手'),
             spot('wiki-konjikido', '中尊寺金色堂', '岩手'),
             spot('iwate-genbikei', '厳美渓', '岩手'),
             spot('wiki-morioka', '盛岡城', '岩手'),
             spot('wiki-ryusendo', '龍泉洞', '岩手'),
             spot('fukuoka-akizuki', '秋月城跡', '福岡')]
    text = ('紅葉色づき情報 最終更新：2026年10月29日（木） 市町村 スポット 色づき状況 例年の見頃 '
            '洋野町 中野白滝 色付き始め 10月下旬～11月上旬 二戸市 馬仙峡 見頃 10月下旬～11月上旬 '
            '盛岡市 盛岡城跡公園（岩手公園） 色付き始め 10月下旬～11月上旬 '
            '八幡平市 八幡平 終盤 9月下旬～10月上旬 八幡平市 松川渓谷 見頃 10月中旬～下旬 '
            '平泉町 中尊寺【世界遺産】 色付き始め 10月下旬～11月上旬 '
            '一関市 厳美渓 色付き始め 10月下旬～11月上旬 '
            '※お出かけの前に現地の情報を確認することをお勧めします。')

    def test_rows_map_to_spots_with_page_date(self):
        reports, error = ud.extract_source(self.text, self.spots, IWATE, TODAY)
        self.assertIsNone(error)
        self.assertEqual(reports['iwate-hachimantai']['status'], 'past')
        self.assertEqual(reports['iwate-chusonji']['status'], 'starting')
        self.assertEqual(reports['wiki-chusonji']['status'], 'starting')
        self.assertEqual(reports['iwate-genbikei']['status'], 'starting')
        self.assertEqual(reports['wiki-morioka']['status'], 'starting')
        self.assertEqual(reports['iwate-genbikei']['observedAt'], '2026-10-29')
        self.assertEqual(reports['iwate-genbikei']['sourceUrl'], IWATE['url'])
        # Not listed on the page, or other prefecture: stays unknown.
        for missing in ('wiki-konjikido', 'wiki-ryusendo', 'fukuoka-akizuki'):
            self.assertNotIn(missing, reports)

    def test_missing_or_stale_page_date_fails_closed(self):
        self.assertEqual(ud.extract_source(self.text.replace('最終更新', '更新'), self.spots, IWATE, TODAY),
                         ({}, 'no-page-date'))
        stale = self.text.replace('2026年10月29日', '2025年11月20日')
        self.assertEqual(ud.extract_source(stale, self.spots, IWATE, TODAY)[1], 'page-date-out-of-range')

    def test_blank_stage_does_not_borrow_next_row(self):
        text = ('最終更新：2026年10月29日 一関市 厳美渓 ー 10月下旬～11月上旬 '
                '二戸市 馬仙峡 見頃 10月下旬～11月上旬')
        reports, _ = ud.extract_source(text, self.spots, IWATE, TODAY)
        self.assertNotIn('iwate-genbikei', reports)

    def test_conflicting_mentions_are_skipped(self):
        text = self.text + ' 一関市 厳美渓 見頃 '
        reports, _ = ud.extract_source(text, self.spots, IWATE, TODAY)
        self.assertNotIn('iwate-genbikei', reports)


class FukuokaTests(unittest.TestCase):
    spots = [spot('wiki-higashi', '東公園 (福岡市)', '福岡'),
             spot('fukuoka-akizuki', '秋月城跡', '福岡'),
             spot('fukuoka-kamado', '宝満宮竈門神社', '福岡'),
             spot('fukuoka-hikosan', '英彦山', '福岡'),
             spot('wiki-ohori', '大濠公園', '福岡')]
    text = ('雷山千如寺大悲王院 糸島市 樹齢400年の大楓。 色づき状況：大楓の上の方が色づき始め（2026/10/7） '
            '秋月城跡 朝倉市 城下町の紅葉。 色づき状況：黒門周辺は青葉（2026/10/29） '
            '雷神社の公孫樹 糸島市 色づき状況：ー '
            '宝満宮竈門神社 太宰府市 色づき状況：見ごろ（2025/11/30） '
            '海の中道海浜公園 福岡市 色づき状況：見ごろ（2026/10/28） '
            '英彦山 添田町 色づき状況：落葉（2025/12/3）')

    def test_labels_bind_to_nearest_preceding_spot(self):
        reports, error = ud.extract_source(self.text, self.spots, FUKUOKA, TODAY)
        self.assertIsNone(error)
        self.assertEqual(reports, {'fukuoka-akizuki': {
            'status': 'green', 'observedAt': '2026-10-29', 'kind': 'official',
            'sourceName': FUKUOKA['name'], 'sourceUrl': FUKUOKA['url'],
            'note': '公式サイトの色づき表記を反映（掲載日）'}})
        # Last season's 竈門神社/英彦山 entries and unlisted 大濠公園 stay off the map.

    def test_label_does_not_leak_to_spot_described_earlier(self):
        # 海の中道 (unknown to us) must not fall back to 秋月 two entries earlier.
        text = '秋月城跡 色づき状況：青葉（2026/10/29） 海の中道海浜公園 色づき状況：見ごろ（2026/10/30）'
        reports, _ = ud.extract_source(text, self.spots, FUKUOKA, TODAY)
        self.assertEqual(reports['fukuoka-akizuki']['status'], 'green')

    def test_description_mentioning_another_spot(self):
        spots = self.spots + [spot('wiki-homanzan', '宝満山', '福岡')]
        text = ('秋月城跡 色づき状況：青葉（2026/10/29） 宝満宮竈門神社 太宰府市 '
                '宝満山の麓にある神社。 色づき状況：見ごろ（2026/10/30）')
        reports, _ = ud.extract_source(text, spots, FUKUOKA, TODAY)
        self.assertEqual(reports['fukuoka-kamado']['status'], 'peak')
        self.assertNotIn('wiki-homanzan', reports)


class RobotsStatusTests(unittest.TestCase):
    def check(self, code):
        import urllib.error
        error = urllib.error.HTTPError('https://example.com/robots.txt', code, 'x', {}, None)
        with patch('update_data.urllib.request.urlopen', side_effect=error):
            return ud.permitted('https://example.com/data/page.html')

    def test_missing_robots_txt_allows_crawl(self):
        self.assertTrue(self.check(404))
        self.assertTrue(self.check(410))

    def test_forbidden_or_server_error_denies_crawl(self):
        for code in (401, 403, 429, 500, 503):
            with self.subTest(code=code):
                self.assertFalse(self.check(code))


class RegionalFetchTests(unittest.TestCase):
    def test_robots_denial_skips_every_source(self):
        with patch('update_data.permitted', return_value=False), patch('update_data.page_text') as fetch:
            reports, diagnostics = ud.regional_reports([], TODAY)
        fetch.assert_not_called()
        self.assertEqual(reports, {})
        self.assertEqual(set(diagnostics.values()), {'robots-denied-or-unavailable'})


JMA_HTML = '''<html><body><h1>かえでの紅葉日 (2025年-2026年)</h1><table>
<tr><th>地点名</th><th colspan="3">2025年</th><th colspan="3">2026年</th><th>代替種目による観測</th></tr>
<tr><th></th><th>観測日</th><th>平年差</th><th>昨年差</th><th>観測日</th><th>平年差</th><th>昨年差</th><th></th></tr>
<tr><td>旭川</td><td>10月22日</td><td>-1</td><td>-3</td><td>10月29日</td><td>+6</td><td>+7</td><td>やまもみじ</td></tr>
<tr><td>札幌</td><td>11月 6日</td><td>+9</td><td>-5</td><td>-</td><td>///</td><td>///</td><td>やまもみじ</td></tr>
<tr><td>東京</td><td>11月23日</td><td>-5</td><td>-10</td><td>-</td><td>///</td><td>///</td><td></td></tr>
</table></body></html>'''


class JmaTests(unittest.TestCase):
    def test_parse_current_year_column(self):
        parsed = ud.parse_jma_table(BeautifulSoup(JMA_HTML, 'html.parser'), 2026)
        self.assertEqual(parsed, {'旭川': '2026-10-29', '札幌': None, '東京': None})
        self.assertIsNone(ud.parse_jma_table(BeautifulSoup(JMA_HTML, 'html.parser'), 2027))

    def test_phenology_payload_keeps_only_observed_events(self):
        soup = BeautifulSoup(JMA_HTML, 'html.parser')
        with patch('update_data.permitted', return_value=True), \
             patch('update_data.page_text', return_value=soup), \
             patch('update_data.amedas_positions', return_value={'旭川': [43.7567, 142.3717], '東京': [35.6917, 139.75]}):
            payload, status = ud.jma_phenology({}, TODAY)
        self.assertTrue(status.startswith('ok (2 stations'))
        stations = {s['name']: s for s in payload['stations']}
        self.assertEqual(stations['旭川']['events']['kaedeKoyo'], '2026-10-29')
        self.assertEqual(stations['東京']['events'], {})
        self.assertNotIn('札幌', stations)  # No coordinates: never placed by guess.
        self.assertEqual(payload['year'], 2026)

    def test_amedas_positions_prefer_weather_office(self):
        table = {'12345': {'type': 'C', 'kjName': '旭川', 'lat': [43, 30.0], 'lon': [142, 0.0]},
                 '12442': {'type': 'A', 'kjName': '旭川', 'lat': [43, 45.4], 'lon': [142, 22.3]}}
        with patch('update_data.permitted', return_value=True), patch('update_data.web_json', return_value=table):
            self.assertEqual(ud.amedas_positions()['旭川'], [43.7567, 142.3717])

    def test_failed_page_keeps_this_seasons_dates(self):
        previous = {'year': 2026, 'stations': [{'name': '金沢', 'lat': 36.5883, 'lon': 136.6333,
                                                'events': {'ichouKoyo': '2026-10-26'}}]}
        observed = JMA_HTML.replace('旭川', '金沢')
        pending = observed.replace('<td>10月29日</td>', '<td>-</td>')
        def fetch(url):
            if url.endswith('phn_012.html'): raise TimeoutError()  # いちょう黄葉 fails
            return BeautifulSoup(observed if url.endswith('phn_014.html') else pending, 'html.parser')
        with patch('update_data.permitted', return_value=True), \
             patch('update_data.page_text', side_effect=fetch), \
             patch('update_data.amedas_positions', return_value={}):
            payload, status = ud.jma_phenology(previous, TODAY)
        kanazawa = {s['name']: s for s in payload['stations']}['金沢']
        self.assertEqual(kanazawa['events'], {'kaedeKoyo': '2026-10-29', 'ichouKoyo': '2026-10-26'})
        self.assertIn('ichouKoyo:TimeoutError', status)

    def test_failure_keeps_previous_payload(self):
        previous = {'year': 2026, 'stations': [{'name': '旭川', 'lat': 1, 'lon': 2, 'events': {}}]}
        with patch('update_data.permitted', return_value=False):
            payload, status = ud.jma_phenology(previous, TODAY)
        self.assertIs(payload, previous)
        self.assertTrue(status.startswith('unavailable'))


if __name__ == '__main__':
    unittest.main()

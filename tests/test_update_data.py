import unittest
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from update_data import extract_nikko,fields_from_issue,parse_verified_issue,merge

class DataUpdateTests(unittest.TestCase):
    def setUp(self):
        self.spots=[{'id':'nikko-ryuzu','nikkoAlias':'竜頭滝'}, {'id':'nikko-yutaki','nikkoAlias':'湯ノ湖、湯滝'}]
    def test_official_extraction(self):
        body='''24 件ありました 〖奥日光〗竜頭滝 現在の状況：◎ 10/17現在 全体的に最盛期。 見頃予測：10月上旬 最終更新日：2026年10月18日 〖奥日光〗湯ノ湖、湯滝 現在の状況：△ 10/17現在 色づき始め 見頃予測：10月中旬 最終更新日：2026年10月18日'''
        rows=extract_nikko(body,self.spots)
        self.assertEqual(rows['nikko-ryuzu']['status'],'full')
        self.assertEqual(rows['nikko-yutaki']['status'],'starting')
        self.assertEqual(rows['nikko-ryuzu']['observedAt'],'2026-10-18')
    def test_verified_issue_security(self):
        fields='''### スポットID\nnikko-ryuzu\n\n### 紅葉状況\n見頃\n\n### 観測日（YYYY-MM-DD）\n2026-10-18\n'''
        issue={'title':'[紅葉レポート] テスト','body':fields,'labels':[{'name':'verified'},{'name':'koyo-report'}],'number':7,'html_url':'https://github.com/Xenoah/map_autumn-leaves/issues/7'}
        import datetime as dt
        self.assertEqual(parse_verified_issue(issue,{'nikko-ryuzu'},dt.date(2026,10,18))[1]['status'],'peak')
        issue['labels'].pop(0)
        self.assertIsNone(parse_verified_issue(issue,{'nikko-ryuzu'},dt.date(2026,10,18)))
    def test_merge_newer(self):
        a={'x':{'status':'green','observedAt':'2026-10-18'}}
        b={'x':{'status':'peak','observedAt':'2026-10-17'}}
        self.assertEqual(merge(a,b,{})['x']['status'],'green')

if __name__=='__main__': unittest.main()

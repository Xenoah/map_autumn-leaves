"""Legacy 2026 Kanto-only bootstrap.

The canonical national inventory is data/spots.json. Running this file without
explicit opt-in would destroy newer prefecture entries, so it is disabled.
"""
import os
if os.environ.get('ALLOW_LEGACY_SEED_RESET') != '1':
    raise SystemExit('Refusing to reset the national spots inventory. Use data/spots.json directly; set ALLOW_LEGACY_SEED_RESET=1 only for a deliberate historical rebuild.')

import json
from pathlib import Path
D=Path(__file__).resolve().parents[1]/'data'
# spot: id,name,region,lat,lon,elev,season,cameraUrl,description,source_title
rows=[
('nikko-ryuzu','竜頭ノ滝','栃木',36.7635,139.4510,1300,'10月上旬〜中旬','','滝と色づく木々を近くで眺められる。','竜頭滝'),
('nikko-yutaki','湯滝・湯ノ湖','栃木',36.7950,139.4289,1480,'10月上旬〜中旬','https://www.nikkoyumoto.com/live_camera/','湯ノ湖と湯滝。温泉旅館組合のライブカメラ案内あり。','湯ノ湖、湯滝'),
('nikko-senjogahara','戦場ヶ原','栃木',36.7760,139.4460,1400,'10月中旬〜下旬','https://www.nikkoyumoto.com/live_camera/','湿原の黄葉と男体山。戦場ヶ原の定点カメラ案内あり。','戦場ヶ原、小田代原の木々'),
('nikko-odashiro','小田代原','栃木',36.7754,139.4302,1430,'9月下旬〜10月中旬','','草紅葉の名所。','小田代原の草紅葉'),
('nikko-chuzenji','中禅寺湖・華厳滝','栃木',36.7363,139.4958,1270,'10月中旬〜11月上旬','https://www.youtube.com/@hotel-kojoen/streams','湖畔の紅葉と八丁出島。中禅寺湖北岸にライブ映像。','中禅寺湖、華厳滝'),
('nikko-iroha','いろは坂','栃木',36.7359,139.5079,1050,'10月中旬〜11月上旬','','標高で色づきが変わる山岳道路。','いろは坂'),
('nikko-kirifuri','霧降高原・キスゲ平','栃木',36.8144,139.6016,1350,'10月上旬〜下旬','','カラマツ・ツツジ類が彩る高原。','日光市霧降高原 キスゲ平園地'),
('nikko-kirifuri-falls','霧降ノ滝','栃木',36.7797,139.6218,720,'10月下旬〜11月上旬','','展望台から落差のある滝を見渡せる。','霧降滝'),
('nikko-temples','日光東照宮周辺','栃木',36.7574,139.5988,640,'11月上旬〜中旬','https://www.nikko-kankou.org/public/features/live-camera','世界遺産の社寺と秋の木々。','世界遺産 日光の社寺'),
('nikko-ryuokyo','龍王峡','栃木',36.8875,139.7140,520,'10月下旬〜11月中旬','','渓谷沿いの遊歩道。','龍王峡'),
('nikko-momiji','日塩もみじライン','栃木',36.9131,139.7745,1100,'10月下旬〜11月上旬','','山頂から麓で進み方が異なる。','日塩もみじライン'),
('nikko-heike','湯西川・平家の里','栃木',36.9620,139.5916,650,'10月中旬〜11月中旬','','茅葺屋根と山あいの紅葉。','平家の里'),
('nasu','那須岳・茶臼岳','栃木',37.1243,139.9634,1680,'9月下旬〜10月中旬','https://www.town.nasu.lg.jp/0030/info-0000000839-1.html','標高により山頂は見頃が早い。那須町の監視カメラ一覧へ。',''),
('shiobara','塩原温泉郷','栃木',36.9705,139.8188,600,'10月下旬〜11月中旬','','箒川沿いの渓谷が美しい。',''),
('akagi','赤城山・大沼','群馬',36.5449,139.1775,1345,'10月中旬〜下旬','','湖畔の紅葉と覚満淵の草紅葉。',''),
('kusatsu','草津温泉・湯畑','群馬',36.6226,138.5973,1200,'10月中旬〜下旬','https://www.kusatsu-onsen.ne.jp/live/index.php','湯畑ほか複数地点の観光協会ライブカメラ。',''),
('haruna','榛名湖','群馬',36.4751,138.8707,1080,'10月下旬〜11月上旬','','カルデラ湖を取り囲む木々。',''),
('tanigawa','谷川岳・天神平','群馬',36.8339,138.9350,1300,'10月上旬〜下旬','https://www.enjoy-minakami.jp/pickup/8339/','谷川岳のロープウェイ周辺。現地カメラ一覧へ。',''),
('terihakyo','照葉峡','群馬',36.8558,139.0407,920,'10月中旬〜下旬','https://www.enjoy-minakami.jp/pickup/8339/','渓谷沿いの紅葉。照葉峡カメラ案内あり。',''),
('ikaho','伊香保温泉・河鹿橋','群馬',36.4979,138.9177,750,'10月下旬〜11月上旬','','朱色の橋とモミジの風景。',''),
('okutama','奥多摩湖','東京',35.7864,139.0368,530,'10月下旬〜11月中旬','','湖畔と奥多摩周辺の紅葉。',''),
('mitake','御岳山','東京',35.7825,139.1489,920,'10月下旬〜11月中旬','','山道と神社周辺の紅葉。',''),
('takao','高尾山','東京',35.6250,139.2436,599,'11月中旬〜下旬','','都心からアクセスしやすい山。',''),
('rikugien','六義園','東京',35.7332,139.7471,20,'11月下旬〜12月上旬','','日本庭園の紅葉。',''),
('jingugaien','明治神宮外苑','東京',35.6767,139.7189,30,'11月中旬〜下旬','','黄金色のイチョウ並木。',''),
('nagatoro','長瀞・月の石もみじ公園','埼玉',36.1048,139.1093,160,'11月上旬〜下旬','','渓谷沿いの紅葉とライトアップ。',''),
('mitsumine','三峯神社','埼玉',35.9248,138.9315,1100,'10月下旬〜11月上旬','','秩父の山深い社。',''),
('chichibu','秩父・中津峡','埼玉',35.9725,138.7949,650,'10月下旬〜11月上旬','','険しい渓谷を見渡せる。',''),
('hakone-ashi','箱根・芦ノ湖','神奈川',35.2046,139.0250,725,'10月下旬〜11月中旬','https://www.hakone.or.jp/7273','湖と山々の紅葉。箱根観光協会のカメラ一覧へ。',''),
('hakone-gora','箱根・強羅','神奈川',35.2497,139.0484,550,'11月上旬〜中旬','https://www.hakone.or.jp/7273','箱根登山鉄道沿線の秋景色。',''),
('oyama','大山・阿夫利神社','神奈川',35.4406,139.2314,700,'11月中旬〜下旬','','丹沢・大山のケーブルカー周辺。',''),
('kamakura','鎌倉・円覚寺','神奈川',35.3371,139.5487,80,'11月下旬〜12月上旬','','古刹と遅い時期の紅葉。',''),
('fukuroda','袋田の滝','茨城',36.7637,140.4077,200,'11月上旬〜中旬','','日本三名瀑のひとつ。',''),
('hananuki','花貫渓谷','茨城',36.7522,140.6206,180,'11月上旬〜中旬','','吊り橋のある紅葉景勝地。',''),
('tsukuba','筑波山','茨城',36.2253,140.1061,877,'11月上旬〜下旬','','山頂から山麓まで時期差が大きい。',''),
('yoro','養老渓谷','千葉',35.2341,140.1659,80,'11月下旬〜12月上旬','','関東でも紅葉が遅いエリア。',''),
('hondoji','本土寺','千葉',35.8423,139.9285,30,'11月下旬〜12月上旬','','松戸の紅葉名所。',''),
('kawaguchi','河口湖・もみじ回廊','山梨',35.5227,138.7714,830,'10月下旬〜11月中旬','https://www.town.fujikawaguchiko.lg.jp/info/info.php?if_id=7','河口湖北岸の紅葉と富士山。町営ライブカメラあり。',''),
('shosenkyo','昇仙峡','山梨',35.7471,138.5615,760,'10月下旬〜11月中旬','','峡谷に連なる巨岩と紅葉。',''),
('kiyosato','清里・美し森','山梨',35.9260,138.4569,1540,'10月中旬〜下旬','','八ヶ岳南麓の高原。',''),
('karuizawa','軽井沢・雲場池','長野',36.3513,138.6300,970,'10月下旬〜11月上旬','','水面に映るモミジが美しい。',''),
('shirakoma','白駒池','長野',36.0554,138.3265,2115,'9月下旬〜10月上旬','','高標高でシーズンが早い。',''),
('kamikochi','上高地・河童橋','長野',36.2507,137.6357,1500,'10月中旬〜下旬','','落葉松と梓川。山岳道路の季節規制に注意。',''),
]
spots=[]
for id,name,pref,lat,lon,elev,season,camera,desc,alias in rows:
    s=dict(id=id,name=name,prefecture=pref,lat=lat,lon=lon,elevation=elev,typicalSeason=season,description=desc)
    if camera: s['camera']={'url':camera,'title':'配信元のライブカメラ'}
    if alias: s['nikkoAlias']=alias
    spots.append(s)
assert len({s['id'] for s in spots})==len(spots)
(D/'spots.json').write_text(json.dumps(spots,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
seed={}
nikko='https://www.nikko-kankou.org/flowering/autumn-leaves'
def add(key, status, dt, source, url, note=''):
 seed[key]=dict(status=status,observedAt=dt,kind='official' if source=='日光市観光協会' else 'third_party',sourceName=source,sourceUrl=url, note=note)
# Official reports: site updated Oct 18, and some reported Oct 15
for id,stat,dt,note in [
 ('nikko-ryuzu','full','2026-10-17','10月17日現在の掲載状況'),
 ('nikko-yutaki','full','2026-10-17','10月17日現在の掲載状況'),
 ('nikko-senjogahara','full','2026-10-17','10月17日現在の掲載状況'),
 ('nikko-odashiro','full','2026-10-17','10月17日現在の掲載状況'),
 ('nikko-chuzenji','peak','2026-10-17','10月17日現在の掲載状況'),
 ('nikko-iroha','starting','2026-10-17','10月17日現在の掲載状況'),
 ('nikko-kirifuri','full','2026-10-17','10月17日現在の掲載状況'),
 ('nikko-ryuokyo','starting','2026-10-18','10月18日更新の掲載状況'),
 ('nikko-momiji','peak','2026-10-18','山頂と麓で色づきに差がある'),
 ('nikko-heike','green','2026-10-15','10月15日更新の掲載状況'),
 ('nikko-kirifuri-falls','green','2026-10-15','10月15日更新の掲載状況'),
 ('nikko-temples','green','2026-09-13','9月13日更新。古い観測につき参考程度'),
]:add(id,stat,dt,'日光市観光協会',nikko,note)
add('nasu','peak','2026-10-17','ウォーカープラス','https://koyo.walkerplus.com/detail/ar0309e394015/','茶臼岳周辺。標高により状況が異なる')
add('fukuroda','green','2026-10-17','ウォーカープラス','https://koyo.walkerplus.com/detail/ar0308e13083/data.html')
add('akagi','starting','2026-10-13','ウェザーニュース','https://www.weathernews.jp/koyo/spot/24216/','10月13日の判定。10月18日頃から見頃の予測あり')
(D/'seed-observations.json').write_text(json.dumps(seed,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(len(spots),'spots',sum(bool(s.get('camera')) for s in spots),'cameras',len(seed),'seed reports')

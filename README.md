# 🍁 KOYO LIVE

**全国の紅葉の現在地を、地図とライブカメラで。** GitHub Pages 完結型のオープンソースプロジェクトです。

> 現地のリアルタイム映像と、定期更新の紅葉状況を併用します。紅葉の色づきは公開情報の更新頻度に左右されるため、秒単位のライブ観測を意味しません。

**🌐 [KOYO LIVE｜全国紅葉マップを開く](https://xenoah.github.io/map_autumn-leaves/)**

![Version](https://img.shields.io/badge/version-1.2.0-e38c58) ![GitHub Pages](https://img.shields.io/badge/deploy-GitHub_Pages-243c30)

## 主な機能

- 🍁 **全国47都道府県・1,083地点**（既存157＋観賞候補926）を収録。追加候補の紅葉状況は観測がない限り「未確認」。
- 🗺️ **軽量OSM地図**：OpenStreetMap標準タイル＋Leaflet。追加の地図・クラスタリングライブラリは使いません。
- 🟠 **6段階**（最盛期／見頃／色づき始め／青葉／終盤／未確認）の色分け
- 🍁 **丸いスポットアイコン**：現地の報告状況に対応した色＋絵文字（赤/橙 🍁、黄/茶 🍂、緑 🌿、未確認 ❔）。📹ピンはカメラ配信元を別タブで開きます。
- 📹 **23地点にカメラリンク**。カメラ付き地点は丸い📹ピン。タップすると配信元サイトを別タブで開きます（動画・定点画像・カメラ案内・期間限定配信を含むため、常時映像を保証しません）。
- 🔎 検索・地方／都道府県選択・色づき段階・カメラ付き地点のフィルター
- 🌤 選択した地点の気温・天気・風速を **Open-Meteo** から取得（10分間キャッシュ）
- 🕓 5分ごとにブラウザがデータ再取得を確認。GitHub Actions は秋季に3時間ごとに再収集
- 🔗 元情報の発表日と出典を明記。**観測から10日以上経過した情報を自動で「未確認」にする**
- ✏️ GitHub Issue Forms を使った現地レポート（スポットIDを詳細画面からコピー可能）。**運営者が `verified` ラベルを付けたもののみ表示**
- 📱 **スマホ優先UI**。地図上に検索・見頃・カメラのクイック操作、片手で開ける大きな一覧シート、44px級タップ領域。一覧は120件ずつ追加表示し、地図マーカーは表示範囲内だけ描画。
- ⚡ 初期HTMLは優先58地点までのバックアップのみ。全国1,083地点は軽量な座標索引から表示し、地点詳細は選んだ都道府県だけを取得。観測情報は5分ごと、索引は1時間ごとに確認。
- 🧭 [追加地点の出典・ライセンス](data/ATTRIBUTION.md)：地名・座標の加工データにCC BY-SA/CC0の条件が適用され、プログラムはMITのまま。

### 地図上のドットの見方

丸いドットの**背景色が確認済みの葉色・紅葉段階**、中央の絵文字がその状態の目印です。未確認の地点は灰色の「❔」で表示し、最新の紅葉状況を推測で補いません。ズームアウト時は複数地点を1つの**丸い集合マーカー**にまとめ、外周の色で含まれる状態の割合を示し、中央の数字で地点数を表示します。ズームインすると個別の色付きドットに戻ります。

## v1.2.0 地点拡大・スマートフォン対応

- Wikipedia/Wikidataを出典とする全国10,640観光地データから、自然景勝地・山・公園・寺社などの観賞**候補**を絞って一度だけ生成します。
- 追加した候補は「現地の紅葉を観測した」とは扱いません。公式データや承認済み報告がない場合は常に「未確認」です。
- 元データとライセンスを明示し、候補各地点からWikipediaの記事に移動できます。
- 📹地点は地図上の大きなカメラマーカーをタップすると配信元が別タブで開き、通常の🍁マーカーは地点詳細を開きます。
- カメラ付き地点を23地点まで拡張（定山渓、田沢湖、角館、志賀高原、御在所岳、阿蘇山など）。公式の案内ページと定点画像も区別。
- スマートフォンで地図を大きく使える検索ツール・下部一覧シート・見頃やカメラの絞り込みを追加。
- 表示範囲外のマーカーを描画せず、一覧も分割して軽量化。初回HTMLに埋め込むのは厳選157地点のみで、全地点はJSONを後から取得。

## v1.1.0 全国対応

- **全47都道府県・157地点**（旧43地点を含む）に拡張。追加地点には、観測情報が確認できない限り「未確認」を表示します。
- 北海道・東北・関東・甲信越・北陸・東海・近畿・中国・四国・九州・沖縄の10地方別に絞り込み。
- 地図を全国表示へ変更。縮小表示ではスポットをまとめ、数字のピンを押すと拡大します。
- 提供元を確認したカメラ案内を5地点追加：旭岳、蔵王・御釜、立山室堂、白川郷、京都嵐山。
- 立山室堂については2026年10月16日付の公式資料に基づく観測値を1件追加（以後10日を超えると未確認に戻ります）。
- **全国の紅葉が3時間ごとに実測更新されるわけではありません。** 現段階の自動観測は日光市観光協会と承認済みGitHub Issueが中心。地方ごとの公式情報は許諾・安定した公開方式を確認でき次第追加します。
- 沖縄県の比地大滝は亜熱帯の自然を紹介する地点。本州のような紅葉最盛期を期待できる地点としては扱いません。
- 新規スポットの座標は地図上の代表点です。登山口、駐車場、撮影地点を保証しません。

## 公開方法（GitHub Pages）

1. **`Xenoah/map_autumn-leaves`** リポジトリの `main` ブランチにソースを配置します。v1.2.0の地点拡張・スマートフォン改修まで反映済みです。
2. リポジトリの **Settings → Actions → General → Workflow permissions** で **Read and write permissions** が必要な場合は有効化します（組織のポリシーで変更不可の場合は管理者に確認）。その後 **Settings → Pages → Build and deployment → Source** を **GitHub Actions** にします。
3. **Actions** タブで `Update foliage data and publish map` の成功を確認します。pushでも自動起動します。
4. `https://xenoah.github.io/map_autumn-leaves/` に反映されます。初回公開までのGitHub側の処理状況はActionsページで確認してください。
5. **Issues → Labels** で `verified`（運営承認）ラベルを作成すると、運営が確認した現地レポートを地図に反映できます。`koyo-report` ラベルは任意です。

### Gitコマンドでの設置

```bash
git clone https://github.com/Xenoah/map_autumn-leaves.git
cd map_autumn-leaves
# このZIPの内容をコピーしてから
git add .
git commit -m "feat: launch KOYO LIVE"
git push origin main
```

`Xenoah`以外のアカウントや別のリポジトリ名に移行する場合は、`assets/app.js` の `REPO`、`scripts/index.template.html` のGitHubリンク、`scripts/update_data.py` の `UA` を変更してください。

## データ更新のしくみ

```text
日光市観光協会の公開情報 ─┐
                         ├─ Python 更新スクリプト ─→ data/live.json ─→ GitHub Pages
承認済み GitHub Issue ───┘                              ↑
                                                    3時間ごと
ブラウザ ───5分ごとに live.json を確認
         ├── Open-Meteo → 現地の気象情報（紅葉実測値とは別）
         └── 📹ボタン → 配信元のライブカメラを新規ウィンドウで表示
```

- 自動収集は `robots.txt` を確認し、許可が確認できない場合は取得しません。
- 初期データ `data/seed-observations.json` には、2026年10月中旬に確認した簡潔な色づき段階と出典を収録しています。**このデータは時間が経過すると未確認表示になります**。
- 各サイトの写真・映像・本文の複製や無断埋め込みはしません。取得する場合も状態を表す記号と更新日のみに限定します。
- 日光観光サイトのDOMや利用ポリシーが変更された場合は取得が止まります。`data/live.json` の `sources` と Actions ログを確認してください。
- 状況更新は情報提供元の公表タイミング次第。ワークフローの成功 ≠ 新しい観測があったこと、です。
- GitHub Actionsの定期実行は遅延することがあります。

### カメラの提供元（全国版追加分）

- [旭岳ロープウェイ（旭岳ライブ画像への案内）](https://asahidake.hokkaido.jp/ja/)
- [蔵王町の御釜ライブカメラ案内](https://town.zao.miyagi.jp/webcamera.html)
- [立山・室堂ライブカメラ](https://www.alpen-route.com/live_camera/murodou.html)
- [白川村の白川郷ライブカメラ](https://cms.vill.shirakawa.lg.jp/livecam/)
- [京都市公式・嵐山渡月橋ライブ配信](https://ja.kyoto.travel/tourism/single01.php?category_id=8&tourism_id=2682)

「ライブカメラあり」は配信元への導線を指します。停止中・季節限定配信・静止画・案内ページを含みます。現在配信中かどうかを保証するアイコンではありません。

### v1.2.0 追加カメラの提供元

- [定山渓観光協会・二見吊橋付近（期間限定）](https://jozankei.jp/)
- [仙北市・田沢湖畔/角館武家屋敷通り](https://www.city.semboku.akita.jp/sightseeing/info/camera.html)
- [志賀高原観光協会・動画/静止画ライブカメラ一覧](https://www.shigakogen.gr.jp/live/index.html)
- [御在所ロープウエイ・山上公園駅カメラ（1分更新、営業時間中のみ）](https://www.gozaisho.co.jp/livecamera/)
- [自然公園財団・阿蘇中岳/草千里4Kライブカメラ](https://www.npfj.or.jp/branch-list/aso/)

※ 📹は配信元が案内・画像を提供していることを示します。現在配信中か、動画か静止画像かは提供元で確認してください。

### レポート承認手順

1. 利用者が地図の「状況を報告」からGitHub Issueを作成。
2. 管理者が地点ID、撮影日時、説明内容を確認。
3. 問題なければIssueに **`verified`** ラベルを追加。次のActions実行で反映されます。
4. 虚偽情報や古い情報を見つけたらラベルを外すと更新が起動します。失敗した場合は手動で再実行してください。

**注意:** `verified` ラベルを付けると公開情報になります。投稿の本文にメールアドレス等の個人情報を含めないでください。

## ファイル一覧

| ファイル | 用途 |
|---|---|
| `index.html` | 公開用HTML。初期データの埋め込みも含む |
| `assets/app.css`, `assets/app.js` | UIと地図の動作 |
| `data/spots.json` | 編集元の全地点データ（Pagesにそのまま配信しない） |
| `data/spots-lite.json` | ブラウザに最初に送る圧縮項目の地点索引（全1,083件） |
| `data/prefectures/*.json` | 詳細表示時だけ読む都道府県別JSON（全47ファイル） |
| `data/catalog-import.done`, `data/ATTRIBUTION.md` | 追加地点の出典・初回取込履歴・ライセンス |
| `data/seed-observations.json` | 初期の色づき観測値と出典 |
| `data/live.json` | GitHub Actionsが生成する公開用の更新データ |
| `scripts/import_spots.py` | 公開座標データから紅葉観賞候補を一度だけ追加（初回のみ） |
| `scripts/build_embedded.py` | 軽量索引・都道府県別詳細データ・縮小HTMLを生成 |
| `scripts/update_data.py` | 公式情報・承認済みレポートの収集・マージ |
| `scripts/build_embedded.py` | オフライン表示用の初期値をHTMLに反映 |
| `.github/workflows/publish.yml` | 定期更新とPages公開 |
| `.github/ISSUE_TEMPLATE/` | 現地報告フォーム |
| `AGENTS.md` | AIエージェント向けの作業規則と参照先 |

## ローカル開発

```bash
python -m pip install -r requirements.txt
python -m unittest discover -s tests -v
SKIP_OFFICIAL=1 python scripts/update_data.py
python scripts/build_embedded.py
python -m http.server 8000
# http://localhost:8000/
```

`index.html`をそのままダブルクリックしても初期の観測一覧は表示されます。ただし地図タイル・地図ライブラリ・気象APIにはインターネット接続が必要です。

## 提供元・ライセンス

- 地図タイル・地理情報: [OpenStreetMap contributors](https://www.openstreetmap.org/copyright) / ODbL ほか
- 現在の気象情報: [Open-Meteo](https://open-meteo.com/) / CC BY 4.0。無償APIは**非商用利用限定**。広告や収益化を行う際はAPI利用条件を再確認してください。
- 紅葉情報の確認元: [日光市観光協会](https://www.nikko-kankou.org/flowering/autumn-leaves)、[ウェザーニュース](https://weathernews.jp/koyo/)、[ウォーカープラス](https://koyo.walkerplus.com/)。独立した情報源であり、当サイトを推奨・監修するものではありません。
- カメラは配信元へのリンクに限ります。停止・移転・通信制限で表示できないことがあります。
- 主要なカメラ提供元: [五千尺ホテル上高地](https://www.gosenjaku.co.jp/live-camera/)、[Mt.T by 星野リゾート](https://tanigawadake-joch.com/mt-t/conditions/)、[清流の宿たむら](https://www.yado-tamura.com/live)。映像の著作権・配信管理権は各提供元に帰属します。
- 追加地点の名称・座標: [rtcode337/travel-log-data](https://github.com/rtcode337/travel-log-data/blob/main/tourist/README.md) 経由のWikipedia（CC BY-SA 4.0）およびWikidata（CC0）。詳細は [data/ATTRIBUTION.md](data/ATTRIBUTION.md)。コードはMIT Licenseですが、派生地点データは別条件です。
- ライブカメラ（追加）: [十和田市・十和田湖](https://www.city.towada.lg.jp/kanko/spot/livecamera.html)、[白馬八方尾根](https://www.happo-one.jp/trekking/livecamera/)（実際の稼働は配信元で確認）。
- コード: MIT License。第三者が保有する地図・データ・映像には本ライセンスは適用されません。

## ロードマップ

- [ ] 他県の観光協会から、データ再利用・自動取得の許諾が得られたフィードを順次追加する
- [ ] スポットごとのタイムライン、過去の紅葉推移
- [ ] ユーザー投稿画像を権利確認後に掲載（初期版では外部リンクのみ）
- [ ] カメラ稼働状況の自動リンクチェック

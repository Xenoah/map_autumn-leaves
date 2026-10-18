# 🍁 KOYO LIVE

**関東・甲信の紅葉の現在地を、地図とライブカメラで。** GitHub Pages 完結型のオープンソースプロジェクトです。

> 現地のリアルタイム映像と、定期更新の紅葉状況を併用します。紅葉の色づきは公開情報の更新頻度に左右されるため、秒単位のライブ観測を意味しません。

![Version](https://img.shields.io/badge/version-1.0.0-e38c58) ![GitHub Pages](https://img.shields.io/badge/deploy-GitHub_Pages-243c30)

## 主な機能

- 🍁 **43スポット**を地図上に表示（東京・神奈川・埼玉・千葉・茨城・栃木・群馬・山梨・長野）
- 🟠 **6段階**（最盛期／見頃／色づき始め／青葉／終盤／未確認）の色分け
- 📹 **11地点にライブカメラリンク**。カメラバッジか詳細のボタンを押すと配信元のページを別ウィンドウで開く（直通カメラと、公式カメラ案内ページを区別して表示）
- 🔎 検索・都県選択・色づき段階・カメラ付き地点のフィルター
- 🌤 選択した地点の気温・天気・風速を **Open-Meteo** から取得（10分間キャッシュ）
- 🕓 5分ごとにブラウザがデータ再取得を確認。GitHub Actions は秋季に3時間ごとに再収集
- 🔗 元情報の発表日と出典を明記。**観測から10日以上経過した情報を自動で「未確認」にする**
- ✏️ GitHub Issue Forms を使った現地レポート（スポットIDを詳細画面からコピー可能）。**運営者が `verified` ラベルを付けたもののみ表示**
- 📱 レスポンシブ対応。ローカルでのHTML直接表示にも初期データを埋め込み

## 公開方法（GitHub Pages）

1. GitHubで公開リポジトリを作成します。推奨名は **`koyo-live-map`**。このプロジェクトのファイルをすべて `main` ブランチ直下に配置してください。ZIP自体をアップするのではなく、展開した**中身**をアップします。
2. リポジトリの **Settings → Actions → General → Workflow permissions** で **Read and write permissions** が必要な場合は有効化します（組織のポリシーで変更不可の場合は管理者に確認）。その後 **Settings → Pages → Build and deployment → Source** を **GitHub Actions** にします。
3. **Actions** タブで `Update foliage data and publish map` を `Run workflow` で一度実行します。最初のpushで実行済みであれば、失敗分を再実行しても構いません。
4. `https://xenoah.github.io/map_autumn-leaves/` に反映されます。初回公開までのGitHub側の処理状況はActionsページで確認してください。
5. **Issues → Labels** で `verified`（運営承認）ラベルを作成すると現地レポートを受け入れられます。`koyo-report` ラベルも作成してください。

### Gitコマンドでの設置

```bash
git clone https://github.com/Xenoah/map_autumn-leaves.git
cd map_autumn-leaves
# このZIPの内容をコピーしてから
git add .
git commit -m "feat: launch KOYO LIVE"
git push origin main
```

`Xenoah`以外のアカウントや別のリポジトリ名で公開する場合は、`assets/app.js` の `REPO`、`scripts/index.template.html` のGitHubリンク、`scripts/update_data.py` の `UA` を変更してください。

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
| `data/spots.json` | スポットの名称・座標・カメラURL |
| `data/seed-observations.json` | 初期の色づき観測値と出典 |
| `data/live.json` | GitHub Actionsが生成する公開用の更新データ |
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
- コード: MIT License。第三者が保有する地図・データ・映像には本ライセンスは適用されません。

## ロードマップ

- [ ] 他県の観光協会から、データ再利用・自動取得の許諾が得られたフィードを順次追加する
- [ ] スポットごとのタイムライン、過去の紅葉推移
- [ ] ユーザー投稿画像を権利確認後に掲載（初期版では外部リンクのみ）
- [ ] カメラ稼働状況の自動リンクチェック

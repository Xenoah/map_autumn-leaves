# AI 開発エージェントへの指示

作業前に `README.md` を読み、GitHub Pages 静的構成を維持してください。用途別の参照先は以下です。

- フロントエンド: `assets/app.js`、`assets/app.css`、`scripts/index.template.html`
- スポット・カメラ追加: `data/spots.json`。カメラURLは配信元の公開ページ、可能なら観光協会等の公式案内で検証する。
- 紅葉報告の信頼性: `data/seed-observations.json`、`scripts/update_data.py`
- 公開・定時実行: `.github/workflows/publish.yml`
- Issueによる観測報告: `.github/ISSUE_TEMPLATE/koyo-report.yml`
- Pythonの検証: `tests/`、`requirements.txt`

## 厳守すること

1. 色づきは出典のある観測報告のみ表示。天気・標高・予想から実測値を創作しない。
2. 紅葉の更新日とパイプラインの実行時刻を混同しない。観測が10日以上古ければ `未確認` にする。
3. ライブカメラ映像は本サイトへコピー・無断埋め込みしない。アイコンは配信元のHTTPSページを `noopener,noreferrer` 付きで新しいタブ／ウィンドウに開く。撮影地点がスポットと異なる場合は説明に明記。
4. 配信元の利用規約と `robots.txt` を守る。確認できない場合は自動収集をスキップ。
5. GitHub Pagesで相対パスが機能することを保ち、鍵をGitに入れない。GitHub Actionsの権限は必要最小限。
6. 変更後に `python -m unittest discover -s tests -v`、`node --check assets/app.js`、`python scripts/build_embedded.py` を実行し、生成 `index.html` もコミット。
7. スポットが増減したらREADMEの収録地点数とカメラ数も更新する。

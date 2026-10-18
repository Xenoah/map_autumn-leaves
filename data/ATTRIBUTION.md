# 地点データの出典・再利用条件

全国の紅葉観賞**候補**として追加した `wiki-` IDのスポットは、
[rtcode337/travel-log-data の tourist/spots.csv](https://github.com/rtcode337/travel-log-data/blob/main/tourist/spots.csv)
（[データ仕様と出典](https://github.com/rtcode337/travel-log-data/blob/main/tourist/README.md)）
に収録された観光地の名称・座標を抽出した加工データです。

- 元の座標は日本語Wikipedia記事の位置情報（**CC BY-SA 4.0**）または Wikidata P625（**CC0**）。ライセンス条件・出典は元データに従います。
- Wikipediaの観光地記事：© Wikipedia contributors, [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/deed.ja)
- Wikidata：Wikidata contributors, [CC0 1.0](https://creativecommons.org/publicdomain/zero/1.0/deed.ja)
- 二次加工：KOYO LIVE。景勝地の種類・知名度ランクで抽出し、元の説明文を再利用せず、観測値とは独立した「紅葉観賞候補」に分類しました。
- 再配布するデータセットではCC BY-SAの同一条件共有・出典表示を遵守してください。サイトのプログラムコード（MIT）とは適用範囲が異なります。
- 各スポットの `sourceUrl` は対応するWikipedia記事です。

**重要：掲載された観賞候補は紅葉の観測地点でも、公式の紅葉名所認定でもありません。**
現在の葉色・見頃は確認できる観測がある地点だけを表示し、観測のない地点は「未確認」にします。
観光地座標の代表点であるため、現地の安全な立入地点・駐車場・撮影地点と一致する保証はありません。

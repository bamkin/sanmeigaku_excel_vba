# 六十の風景 — 開発リポジトリ

仕様はすべて docs/ にある。最初に docs/00_仕様書.md を読むこと。

## 最初の指示（Claude Codeに渡す五行）

1. docs/00_仕様書.md を読み、開発順序1（算出層）だけを実装する
2. 技術構成は仕様書の「8. 技術的な決定」に従う
3. 算出は docs/60_算出手順.md に従い、テストケース6件がpytestで全項目一致するまで次へ進まない
4. 節入日は天文計算でJSONを生成する。干支暦の画像は渡さない。突合は逆井が行う
5. 教材由来の呼び名は docs/45_六十花甲子_照合表.md の中だけに置き、出力に出さない

## 算出層（開発順序1・実装済み）

```
pip install -r requirements-dev.txt      # pytest と ephem（節入日の生成にだけ使う）
python -m pytest                         # テストケース6件＋早見表の総当たり
python -m sanmei 1973-11-23 male         # 宿命表をテキスト表示
python -m sanmei 1973-11-23 male --json  # 宿命表JSON
python scripts/gen_setsu.py --year 1974  # 節入日の時刻を1年ぶん表示（突合用）
```

`sanmei/` は依存なしの純Python。Python から使うときは `from sanmei import compute_destiny`。
実装上の判断と教材との食い違いは docs/61_算出層_実装メモ.md にまとめてある。
節入日JSON（sanmei/data/setsu.json）は 1974年・1930年を干支暦と突合済み（2026-10-14）。

## 生成層（開発順序2・実装済み、実機サンプルあり）

```
pip install -r requirements-dev.txt      # anthropic SDK を含む
export ANTHROPIC_API_KEY=...             # Claude Code のクラウド環境では ROKUJU_ANTHROPIC_API_KEY（下記）
python -m seisei --birth 1973-11-23 --sex male --answers samples/1973-11-23_申込回答.json --name "逆井 勤" --out out.md
python -m seisei ... --dry-run           # API を呼ばずプロンプトだけ書き出す
python -m seisei --check 鑑定書.md        # 禁則チェックだけ通す
```

`seisei/` はシステムプロンプトを docs/10・29・40・00（構成と禁則）・50・30〜39 から組み立て、生成後に風景を差し込み、禁則チェック（docs/45 の教材呼び名、docs/00 の禁則語、見出し、文字数、文体の頻度制限）を通す。
実装判断と確認待ちは docs/62_生成層_実装メモ.md。実機で生成した鑑定書は samples/1973-11-23_実機.md（2026-10-14、claude-opus-5-5。docs/50 の五行訂正後に取り直したものが 1973-11-23_実機2.md）、docs/50 との差と二回の違いは samples/1973-11-23_比較.md。

### 実機でサンプルを生成して比較を更新する

1. Anthropic のコンソールで API キーを発行し、環境変数に入れる：`export ANTHROPIC_API_KEY=sk-ant-...`
   - **Claude Code のクラウド環境で動かすとき**は、環境の設定に `ROKUJU_ANTHROPIC_API_KEY=sk-ant-...` の名前で入れる。クラウド環境は Claude Code 自身の認証を守るため `ANTHROPIC_API_KEY` という名前の変数をセッションに渡さない（保存しても消える）。`seisei` は `ANTHROPIC_API_KEY` が無ければ `ROKUJU_ANTHROPIC_API_KEY` を API キーとして使う（`seisei/generate.py` の `api_key_from_env`）。ローカルでは `ANTHROPIC_API_KEY` のままでよい
2. 生成する（1973-11-23 男性、申込回答は samples/ のもの。`--today` は年運の「今年」を固定するため）：
   ```
   python -m seisei --birth 1973-11-23 --sex male --answers samples/1973-11-23_申込回答.json \
     --name "逆井 勤" --today 2026-10-14 --out samples/1973-11-23_実機.md
   ```
   `samples/1973-11-23_実機.md`（風景差し込み済み）と `samples/1973-11-23_実機.raw.md`（モデル出力そのまま）ができ、禁則チェックの結果と usage が表示される
3. 数字の比較を出す：`python scripts/compare_report.py samples/1973-11-23_実機.md docs/50_鑑定書サンプル.md`
4. `samples/1973-11-23_比較.md` の「数字」の表を 3 の出力で置き換え、構成・文体・内容の差を読んで書き直す。セッション内で書いたサンプル（`1973-11-23_生成サンプル.md`）は手本として残してよいが、比較の本番は実機の出力
5. モデルや effort を変えて取り直すときは `--model` `--effort`（既定 claude-opus-5-5 / high）。出力ファイル名を変えて並べる

## 無料診断（開発順序3・実装済み）

```
uvicorn shindan.app:app --reload     # http://127.0.0.1:8000/
python scripts/dump_shindan.py       # 60本の一段落・結びと、構造の一言25通りを samples/ に書き出す
```

生年月日 → 番号・干支・自前の名・季節・風景の一段落・構造の一言（定型、LLM不使用）・風景カード（SVG）。詳細は docs/63_無料診断_実装メモ.md。

## 受付（開発順序4・実装済み）と製本（開発順序5・実装済み）

```
uvicorn shindan.app:app --reload                         # /apply → 決済 → 生成 → /admin で承認 → 送付
ROKUJU_GENERATOR=dummy uvicorn shindan.app:app --reload  # API を呼ばず、samples の実機2 で導線を通す
python scripts/get_fonts.py                              # PDF 用に Noto Serif JP を fonts/ へ（一度だけ）
python -m seihon samples/1973-11-23_実機2.md --birth 1973-11-23 --sex male --name "逆井 勤" --out out.pdf
```

`uketsuke/` が申込・決済・生成・承認・送付（SQLite、アダプタは環境変数で Stripe／Resend／Claude とダミーを切り替え。鍵が無ければダミーで全導線が通る）。`seihon/` が鑑定書 Markdown → PDF（WeasyPrint、Noto Serif JP、水墨のトーン）。
承認画面は `/admin`（`ROKUJU_ADMIN_PASSWORD` で Basic 認証）。環境変数の一覧と決めたことは docs/64_受付_実装メモ.md、PDF の体裁は docs/65_製本_実装メモ.md。Railway 用の Dockerfile あり。

## docs/ の一覧

| ファイル | 役割 | 使う層 |
|---|---|---|
| 00_仕様書.md | 商品・導線・二層アーキテクチャ・技術決定 | 全体 |
| 10_文体ガイド.md | 鑑定書・風景・SNSの文体と禁則 | 生成層 |
| 20_申込フォーム.md | 5問＋任意1問と各問いの用途 | Web層・生成層 |
| 29_風景_書き方の約束.md | 風景の執筆規則 | 生成層（参照のみ） |
| 30〜39_風景_甲〜癸.md | 六十の風景の本文（差し込み用、生成しない） | 生成層・無料診断・PDF |
| 40_学理リファレンス.md | 算命学の学理要約（教材の呼び名なし） | 生成層プロンプト |
| 45_六十花甲子_照合表.md | 番号・干支・風景の名・従星・教材の呼び名 | 算出層のみ。禁則語リストの元 |
| 50_鑑定書サンプル.md | 生成層の手本 | 生成層プロンプト |
| 60_算出手順.md | 算出の規則・早見表・テストケース6件 | 算出層 |
| 61_算出層_実装メモ.md | 算出層の実装判断・教材との食い違い（確認済み） | 算出層 |
| 62_生成層_実装メモ.md | 生成層の実装判断・API設定・確認待ち | 生成層 |
| 63_無料診断_実装メモ.md | 無料診断の構成・構造の一言の定型・確認待ち | Web層 |
| 64_受付_実装メモ.md | 申込・決済・生成・承認・送付の経路・状態・環境変数 | Web層 |
| 65_製本_実装メモ.md | PDF の体裁・フォント・確認待ち | PDF |

## リポジトリに入れないもの

教材のPDF・画像（干支暦を含む）、鑑定アプリの出力PDF。

## 旧ツール

`sanmeigaku_analysis.xlsm.xlsm` は以前の Excel VBA 版（生年月日・生時・性別から干支・蔵干・通変星・十二大従星・宿命中殺を出す）。新しい算出層とは独立で、参照用に残してある。

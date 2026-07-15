# pyser

Python製の自作ブラウザ（学習用プロジェクト）。

参考: https://github.com/negibokken/web-browser-engineering-step-by-step/commits/main/

## 構成

すべて `main.py` に実装されている。

| クラス | 役割 |
| --- | --- |
| `URL` | URL文字列をパースし、TCP/SSLソケットでHTTPリクエストを送信してレスポンスボディ（HTML文字列）を取得する |
| `Text` | HTMLのテキストノード（`children`, `parent`を持つ） |
| `Element` | HTMLのタグ要素ノード（`tag`, `attributes`, `children`, `parent`を持つ） |
| `HTMLParser` | HTML文字列を1文字ずつ読み、`Text`/`Element`からなるDOM木を構築する。省略タグ（`html`/`head`/`body`）の補完も行う |
| `DocumentLayout` | レイアウト木のルート。DOM木のルートノードを受け取り、`layout()`で唯一の子として`BlockLayout`を1つ生成し、そのレイアウト結果（`display_list`）を自身にコピーする |
| `BlockLayout` | DOM木と対になるレイアウト木のノード。`node`（対応するDOMノード）、`parent`、`previous`（兄弟レイアウト、現状未使用）、`children`（子レイアウト）を持つ。`layout_mode()`でノードが`"block"`（`BLOCK_ELEMENTS`に含まれる子要素を持つ、または子を持たない）か`"inline"`（テキストノード、またはインライン要素のみを子に持つ）かを判定し、`layout()`はそれに応じて分岐する：`"block"`ならDOM子ノードごとに`BlockLayout`を生成して再帰的に`layout()`、`"inline"`なら文字の折り返し・行送り・スタイル（太字/斜体/サイズ）を計算して`display_list`を生成する |
| `Browser` | 全体を統括。tkinterの`Canvas`を保持し、`load()`でURL取得→パース→レイアウトを行い、`draw()`で画面に描画する。スクロール操作も管理 |

`get_font()`（モジュール関数）は`FONTS`辞書でフォントをキャッシュし、`BlockLayout`から利用される。

## データフローの流れ

```
URL ── request() ──▶ HTML文字列
                        │
                        ▼
HTMLParser ── parse() ──▶ Element/Text の木（DOM）
                        │
                        ▼
DocumentLayout ── layout() ──▶ BlockLayout を生成
                        │
                        ▼
BlockLayout ── layout()/recurse() ──▶ display_list（描画命令）
                        │
                        ▼
Browser.draw() ──▶ tkinter Canvas に描画
```

`Browser`が起点となり、`URL → HTMLParser → DocumentLayout → BlockLayout`の順にパイプラインとしてデータを渡していく設計。レイアウト部分はDOM木と対になる「レイアウト木」（`DocumentLayout`をルートに`BlockLayout`がぶら下がる構造）に分離された。`BlockLayout`はDOM木の構造（ブロック要素かインライン要素か）に応じて`"block"`/`"inline"`を判定し、ブロックノードの下にはさらに`BlockLayout`の子を再帰的に作る。

## 現在の挙動（実装状況スナップショット）

- **対応スキーム**: `http`, `https`（`URL`クラスがホスト/ポート/パスをパースし、`https`はSSLでラップ）。ポート番号のホスト指定（`host:port`）にも対応。
- **HTTP通信**: HTTP/1.0でGETリクエストのみ送信。レスポンスの`transfer-encoding`・`content-encoding`ヘッダーがある場合はassertで落ちる（chunked encodingや圧縮レスポンスは未対応）。
- **HTML解析**: `HTMLParser`が1文字ずつ読んでDOM木（`Element`/`Text`）を構築。
  - 自己終了タグ（`br`, `img`, `hr`など）に対応。
  - `html`/`head`/`body`タグが省略されたHTMLでも暗黙的に補完する（`implicit_tags`）。
  - コメントやDOCTYPE（`<!...>`）は無視。属性値のクォート（`'`/`"`）除去に対応。
- **レイアウト**: `DocumentLayout` → `BlockLayout`の木構造でDOM木に対応するレイアウト木を構築。
  - `BlockLayout.layout_mode()`でノードごとに`"block"`/`"inline"`を判定し、`"block"`ノードは子ごとに`BlockLayout`を再帰生成、`"inline"`ノードはテキストの折り返し・行送りを計算。
  - インライン処理では`<b>`（太字）、`<i>`（斜体）、`<small>`/`<big>`（フォントサイズ±）、`<br>`（改行）、`</p>`（段落間スペース）に対応。フォントは`get_font()`でキャッシュされる。
  - ⚠️ **既知の未実装**: 子`BlockLayout`が生成した`display_list`を親（ブロックノード）に集約する処理がまだない。ルートノード（`html`）は基本的に`"block"`モードになるため、`DocumentLayout.display_list`は現状常に空になり、**画面には何も描画されない**。次のステップで集約処理（本でいう`paint()`相当）を実装する必要がある。
- **描画/操作**: tkinterの800x600ウィンドウ・キャンバスを1つ生成。下矢印キーで100pxずつスクロール。ウィンドウリサイズやマウス操作には未対応。
- **未対応・既知の制限**:
  - CSSは一切未対応（色、余白、フォント指定など）。
  - リンク遷移やフォーム送信は未対応（クリック操作自体が未実装）。
  - リダイレクト、キャッシュ、Cookieなど高度なHTTP機能は未対応。
  - 画像・テーブルなど非テキスト要素の実際の描画は未対応（DOM/レイアウト木には現れるが中身は描かれない）。

## 実行方法

```
python main.py <URL>
```

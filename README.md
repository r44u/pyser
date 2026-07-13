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
| `BlockLayout` | DOM木を再帰的に巡回し、文字の折り返し・行送り・スタイル（太字/斜体/サイズ）を計算して描画命令リスト `display_list` を生成する。`node`（対応するDOMノード）、`parent`（`DocumentLayout`）、`previous`（兄弟レイアウト、現状未使用）を持つ |
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

`Browser`が起点となり、`URL → HTMLParser → DocumentLayout → BlockLayout`の順にパイプラインとしてデータを渡していく設計。レイアウト部分はDOM木と対になる「レイアウト木」（`DocumentLayout`をルートに`BlockLayout`がぶら下がる構造）に分離された。

## 実行方法

```
python main.py <URL>
```

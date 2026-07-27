# pyser

Python製の自作ブラウザ（学習用プロジェクト）。

参考: https://github.com/negibokken/web-browser-engineering-step-by-step/commits/main/

## 構成

`main.py`にブラウザ本体を実装。`browser.css`はブラウザ組み込みのデフォルトスタイルシート。

| クラス/関数 | 役割 |
| --- | --- |
| `URL` | URL文字列をパースし、TCP/SSLソケットでHTTPリクエストを送信してレスポンスボディを取得する。`resolve()`で相対URL（パス相対・スキーム相対・ホスト相対）を絶対URLに解決する |
| `Text` | HTMLのテキストノード（`children`, `parent`を持つ） |
| `Element` | HTMLのタグ要素ノード（`tag`, `attributes`, `children`, `parent`, `style`を持つ） |
| `HTMLParser` | HTML文字列を1文字ずつ読み、`Text`/`Element`からなるDOM木を構築する。省略タグ（`html`/`head`/`body`）の補完も行う |
| `tree_to_list()` | DOM木（またはレイアウト木）を再帰的に辿り、フラットなリストに変換するユーティリティ関数 |
| `TagSelector` | タグ名が一致するかを判定するCSSセレクタ。詳細度`priority = 1` |
| `DescendantSelector` | 子孫結合子（例: `p a`）を判定するCSSセレクタ。`ancestor`/`descendant`の2つのセレクタを持ち、`priority`は両者の合計 |
| `CSSParser` | CSSテキストをパースする。`プロパティ:値;`のペア列（`body()`）と、`セレクタ { ... }`形式のルールブロック列（`selector()`/`parse()`）の両方に対応。構文エラー時は`;`/`}`まで読み飛ばして復帰する |
| `cascade_priority()` | ルール`(selector, body)`から`selector.priority`を取り出す関数。ルールを詳細度順にソートするための`key`として使う |
| `style()` | DOM木を再帰的に辿り、各ノードの`node.style`辞書を構築する。継承・カスケード適用・インラインstyle・`%`指定font-sizeの解決を行う（詳細は下記） |
| `DocumentLayout` | レイアウト木のルート。DOM木のルートノードを受け取り、`layout()`で唯一の子として`BlockLayout`を1つ生成し、そのレイアウト結果（`display_list`）と`height`を自身にコピーする |
| `BlockLayout` | DOM木と対になるレイアウト木のノード。`node`（対応するDOMノード）、`parent`、`previous`（兄弟レイアウト）、`children`（子レイアウト）、および`x`/`y`/`width`/`height`の絶対座標を持つ。`layout_mode()`でノードが`"block"`（`BLOCK_ELEMENTS`に含まれる子要素を持つ、または子を持たない）か`"inline"`（テキストノード、またはインライン要素のみを子に持つ）かを判定し、`layout()`はそれに応じて分岐する：`"block"`ならDOM子ノードごとに`BlockLayout`を生成して再帰的に`layout()`、`"inline"`なら`recurse()`/`word()`/`flush()`によって文字の折り返し・行送り・スタイルを計算して`display_list`（`(x, y, word, font, color)`の単語ごとの絶対座標付きタプル）を生成する |
| `DrawText` | 文字列を描画するコマンドオブジェクト。`top`/`left`/`bottom`/`color`を持ち、`execute(scroll, canvas)`でtkinter Canvasに指定色で文字を描く |
| `DrawRect` | 矩形を描画するコマンドオブジェクト。`top`/`left`/`bottom`/`right`/`color`を持ち、`execute(scroll, canvas)`でtkinter Canvasに塗りつぶし矩形を描く（`width=0`で枠線なし） |
| `paint_tree()` | レイアウト木を再帰的に辿り、各ノードの`paint()`が返す描画コマンド（`DrawText`/`DrawRect`）を`display_list`に集約するモジュール関数 |
| `Browser` | 全体を統括。tkinterの`Canvas`を保持し、`load()`でURL取得→パース→スタイルシート収集・適用→レイアウト→描画コマンド集約を行い、`draw()`で画面に描画する。スクロール操作も管理 |

`get_font()`（モジュール関数）は`FONTS`辞書でフォント（と内部で生成する`Label`）をキャッシュし、`BlockLayout.word()`から利用される。
`print_tree()`（モジュール関数）はデバッグ用にDOM木/レイアウト木を標準出力にダンプする。
`INHERITED_PROPERTIES`（モジュール定数）は継承されるCSSプロパティ（`font-size`/`font-style`/`font-weight`/`color`）のデフォルト値。
`BLOCK_ELEMENTS`（モジュール定数）は`layout_mode()`が`"block"`と判定するタグ名の一覧（`p`/`div`/`h1`〜`h6`/`ul`/`li`/`table`など）。
`DEFAULT_STYLE_SHEET`（モジュール定数）はモジュール読み込み時に`browser.css`をパースした結果で、全ページに適用されるブラウザ標準スタイル。

## データフローの流れ

```
URL ── request() ──▶ HTML文字列
                        │
                        ▼
HTMLParser ── parse() ──▶ Element/Text の木（DOM）
                        │
                        ▼
<link rel=stylesheet> を収集 → url.resolve() で絶対URL化 → request() で外部CSS取得
                        │
                        ▼
DEFAULT_STYLE_SHEET + 外部CSSのルール列 を cascade_priority でソート
                        │
                        ▼
style() ──▶ 各ノードに node.style をセット（継承 → カスケード適用 → インラインstyle → %指定font-size解決）
                        │
                        ▼
DocumentLayout ── layout() ──▶ BlockLayout木を生成し、絶対座標(x, y, width, height)を計算
                        │        (inlineノードは recurse()/word()/flush() で display_list を構築)
                        ▼
paint_tree() ──▶ 各レイアウトノードの paint() を集約し display_list（DrawText/DrawRectのリスト）を構築
                        │
                        ▼
Browser.draw() ──▶ 各コマンドの execute() を呼び tkinter Canvas に描画
```

`Browser`が起点となり、`URL → HTMLParser → (スタイルシート収集) → style → DocumentLayout/BlockLayout → paint_tree`の順にパイプラインとしてデータを渡していく設計。レイアウト部分はDOM木と対になる「レイアウト木」（`DocumentLayout`をルートに`BlockLayout`がぶら下がる構造）に分離されている。`BlockLayout`はDOM木の構造（ブロック要素かインライン要素か）に応じて`"block"`/`"inline"`を判定し、ブロックノードの下にはさらに`BlockLayout`の子を再帰的に作る。描画はレイアウト木から直接Canvas APIを呼ぶのではなく、`DrawText`/`DrawRect`という中間コマンドオブジェクトを経由する（`paint()`→`paint_tree()`→`execute()`）。

## 現在の挙動（実装状況スナップショット）

- **対応スキーム**: `http`, `https`（`URL`クラスがホスト/ポート/パスをパースし、`https`はSSLでラップ）。ポート番号のホスト指定（`host:port`）にも対応。`resolve()`により相対URL（通常/パス相対/スキーム相対/ホスト相対、`../`の遡上を含む）を絶対URLに解決できる。
- **HTTP通信**: HTTP/1.0でGETリクエストのみ送信。レスポンスの`transfer-encoding`・`content-encoding`ヘッダーがある場合はassertで落ちる（chunked encodingや圧縮レスポンスは未対応）。
- **HTML解析**: `HTMLParser`が1文字ずつ読んでDOM木（`Element`/`Text`）を構築。
  - 自己終了タグ（`br`, `img`, `hr`など）に対応。
  - `html`/`head`/`body`タグが省略されたHTMLでも暗黙的に補完する（`implicit_tags`）。
  - コメントやDOCTYPE（`<!...>`）は無視。属性値のクォート（`'`/`"`）除去に対応。
- **CSS解析・適用**: `CSSParser`がプロパティ宣言（`prop:val;`）とルールブロック（`selector { ... }`）の両方をパース可能。`TagSelector`/`DescendantSelector`でタグ名一致・子孫結合子のマッチングに対応し、それぞれ詳細度（`priority`）を持つ。
  - `Browser.load()`が`browser.css`（デフォルトスタイル）＋ページ内の`<link rel="stylesheet">`が指す外部CSS（`url.resolve()`で絶対URL化して取得、失敗時はスキップ）を全て集め、`cascade_priority`で詳細度順にソートしてから`style()`に渡す＝簡易的なCSSカスケードを実装。
  - `style()`は各ノードで (1)`INHERITED_PROPERTIES`（`font-size`/`font-style`/`font-weight`/`color`）を親から継承 → (2)マッチするスタイルシートルールを詳細度順に上書き適用 → (3)インライン`style`属性を最優先で適用 → (4)`font-size`が`%`指定なら親のfont-sizeを基準にpx換算、の順で`node.style`を決定する。
  - `browser.css`は`pre`（グレー背景）、`a`（青文字）、`i`（斜体）、`b`（太字）、`small`（90%サイズ）、`big`（110%サイズ）のデフォルトルールを定義。`<b>`/`<i>`/`<small>`/`<big>`のようなタグ固有の見た目は、レイアウト側でタグ名を特別扱いするのではなく、これらのCSSルールが`node.style`に反映されることで実現している。
- **レイアウト**: `DocumentLayout` → `BlockLayout`の木構造でDOM木に対応するレイアウト木を構築し、各ノードが絶対座標（`x`/`y`/`width`/`height`）を持つ。
  - `BlockLayout.layout_mode()`でノードごとに`"block"`/`"inline"`を判定し、`"block"`ノードは子ごとに`BlockLayout`を再帰生成、`"inline"`ノードは`recurse()`でDOM木を辿ってテキストを単語分割しながら`word()`を呼ぶ。
  - `word()`は`node.style`の`font-size`/`font-weight`/`font-style`/`color`から`get_font()`でフォントを取得し（キャッシュあり）、単語幅を測って行の折り返し判定（幅超過なら`flush()`）を行い、行バッファ（`x`オフセット・単語・フォント・色）に追加する。
  - `flush()`は行内の最大アセント/ディセントから行間1.25倍でベースラインと次の行のy座標を計算し、各単語を絶対座標`(x, y, word, font, color)`として`display_list`に確定させる。
  - `<br>`は`flush()`を呼んで改行するのみ。太字/斜体/サイズ切り替えや段落間スペースはタグ名のハードコードではなく、CSSカスケードで決まった`node.style`を`word()`が参照することで実現している。
  - 各レイアウトノードの`paint()`が描画コマンド（`DrawText`/`DrawRect`）を生成し、`paint_tree()`がレイアウト木全体を辿って1つの`display_list`に集約する。
- **描画**: `<pre>`要素はグレー背景の矩形を描画（`browser.css`の`pre { background-color: gray; }`ルール経由）。`background-color`スタイルが指定された任意の要素は、その色で背景矩形を描画。テキストは`node.style["color"]`（CSSカスケードで決定された色。デフォルトは黒、`a`要素はデフォルトで青）で描画される。
- **画面/操作**: tkinterの800x600ウィンドウ・キャンバスを1つ生成。下矢印キーで100pxずつスクロール、`document.height`を基にスクロール量の上限をクランプ。ウィンドウリサイズやマウス操作には未対応。
- **未対応・既知の制限**:
  - CSSプロパティは`background-color`・`color`・`font-size`・`font-style`・`font-weight`以外は未対応（余白・幅・レイアウト系プロパティなど）。マージン/パディングがないため、段落（`<p>`）同士の間に明示的な追加スペースは入らない。
  - `<style>`タグによる内部スタイルシート（HTML埋め込みCSS）は未対応。読み込まれるのは`browser.css`と`<link rel="stylesheet">`の外部CSSのみ。
  - リンク遷移やフォーム送信は未対応（クリック操作自体が未実装。`URL.resolve()`は実装済みだがスタイルシート取得以外では未使用）。
  - リダイレクト、キャッシュ、Cookieなど高度なHTTP機能は未対応。
  - 画像・テーブルなど非テキスト要素の実際の描画は未対応（DOM/レイアウト木には現れるが中身は描かれない）。

## 実行方法

```
python main.py <URL>
```

`main.py`と同じディレクトリに`browser.css`が必要（`DEFAULT_STYLE_SHEET`としてモジュール読み込み時に参照される）。

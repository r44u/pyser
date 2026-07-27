import socket
import ssl
import tkinter
import tkinter.font
from typing import Literal


WIDTH, HEIGHT = 800, 600
HSTEP, VSTEP = 13, 18  # 水平・垂直ステップ
SCROLL_STEP = 100
FONTS = {}
BLOCK_ELEMENTS = [
    "html",
    "body",
    "article",
    "section",
    "nav",
    "aside",
    "h1",
    "h2",
    "h3",
    "h4",
    "h5",
    "h6",
    "hgroup",
    "header",
    "footer",
    "address",
    "p",
    "hr",
    "pre",
    "blockquote",
    "ol",
    "ul",
    "menu",
    "li",
    "dl",
    "dt",
    "dd",
    "figure",
    "figcaption",
    "main",
    "div",
    "table",
    "form",
    "fieldset",
    "legend",
    "details",
    "summary",
]
INHERITED_PROPERTIES = {
    "font-size": "16px",
    "font-style": "normal",
    "font-weight": "normal",
    "color": "black",
}


class DrawText:
    def __init__(self, x1, y1, text, font, color):
        self.top = y1
        self.left = x1
        self.text = text
        self.font = font
        self.bottom = y1 + font.metrics("linespace")
        self.color = color

    def execute(self, scroll, canvas):
        canvas.create_text(
            self.left,
            self.top - scroll,
            text=self.text,
            font=self.font,
            anchor="nw",
            fill=self.color,
        )


class DrawRect:
    def __init__(self, x1, y1, x2, y2, color):
        self.top = y1
        self.left = x1
        self.bottom = y2
        self.right = x2
        self.color = color

    def execute(self, scroll, canvas):
        canvas.create_rectangle(
            self.left,
            self.top - scroll,
            self.right,
            self.bottom - scroll,
            width=0,  # デフォルトでは1ピクセルの線が引かれるため0にする,
            fill=self.color,
        )


def get_font(size, weight, style):
    # フォントキャッシュからフォントを取得または作成する関数
    key = (size, weight, style)
    if key not in FONTS:
        # キャッシュにない場合は新しいフォントを作成
        font = tkinter.font.Font(size=size, weight=weight, slant=style)
        # パフォーマンス向上のためのLabelオブジェクト（Tkinterの推奨）
        label = tkinter.Label(font=font)
        FONTS[key] = (font, label)
    # キャッシュからフォントオブジェクトを返す
    return FONTS[key][0]


class URL:
    # コンストラクタ: URL文字列を受け取り、オブジェクトを初期化します
    def __init__(self, url):
        # スキームと残りのURLを分割します
        self.scheme, url = url.split("://", 1)
        # スキームが 'http' または 'https' であることを確認します
        assert self.scheme in ["http", "https"]
        if self.scheme == "http":
            self.port = 80
        elif self.scheme == "https":
            self.port = 443
        if "/" not in url:
            url = url + "/"
        # ホストと残りのURL（パス）を分割します
        self.host, url = url.split("/", 1)
        # ホスト名にポートが含まれているか確認します
        if ":" in self.host:
            # ホスト名とポート番号を分割します
            self.host, port = self.host.split(":", 1)
            # ポート番号を整数に変換します
            self.port = int(port)
        # パスを '/' から始まるように設定します
        self.path = "/" + url

    def request(self):
        # TCP/IPソケットを作成します
        s = socket.socket(
            family=socket.AF_INET,  # IPv4アドレスファミリー
            type=socket.SOCK_STREAM,  # ストリームソケットタイプ (TCP)
            proto=socket.IPPROTO_TCP,  # TCPプロトコル
        )
        # 指定されたホストとポートに接続します
        s.connect((self.host, self.port))

        # HTTPSスキームの場合、SSL/TLSでソケットをラップします
        if self.scheme == "https":
            ctx = ssl.create_default_context()
            s = ctx.wrap_socket(s, server_hostname=self.host)

        # GETリクエスト文字列を作成します
        request = "GET {} HTTP/1.0\r\n".format(self.path)
        # Hostヘッダーを追加します
        request += "Host: {}\r\n".format(self.host)
        # ヘッダーの終わりを示す空行を追加します
        request += "\r\n"
        # リクエストをUTF-8でエンコードして送信します
        s.send(request.encode("utf8"))
        response = s.makefile("r", encoding="utf8", newline="\r\n")

        # レスポンスの最初の行（ステータスライン）を読み取ります
        statusline = response.readline()
        # ステータスラインをバージョン、ステータスコード、説明に分割します
        version, status, explanation = statusline.split(" ", 2)

        # レスポンスヘッダーを格納するディクショナリを初期化します
        response_headers = {}
        # ヘッダーを読み取るループ
        while True:
            line = response.readline()
            # 空行はヘッダーの終わりを示します
            if line == "\r\n":
                break
            # ヘッダー名と値をコロンで分割します
            header, value = line.split(":", 1)
            # ヘッダー名を小文字に正規化し、値の前後の空白を削除してディクショナリに追加します
            response_headers[header.casefold()] = value.strip()
        # Transfer-Encodingヘッダーがないことを確認します
        assert "transfer-encoding" not in response_headers
        # Content-Encodingヘッダーがないことを確認します
        assert "content-encoding" not in response_headers

        content = response.read()
        # ソケットを閉じます
        s.close()
        # ... (ボディ読み取り、ソケットクローズ)
        # レスポンスのボディを返します
        return content

    def resolve(self, url):
        # 通常のURL
        if "://" in url:
            return URL(url)
        # パス相対URL
        if not url.startswith("/"):
            dir, _ = self.path.rsplit("/", 1)
            while url.startswith("../"):
                _, url = url.split("/", 1)
                if "/" in dir:
                    dir, _ = dir.rsplit("/", 1)
            url = dir + "/" + url
        # スキーム相対URL
        if url.startswith("//"):
            return URL(self.scheme + ":" + url)
        # ホスト相対URL
        else:
            return URL(self.scheme + "://" + self.host + ":" + str(self.port) + url)


class Text:
    def __init__(self, text, parent):
        self.text = text
        self.children = []
        self.parent = parent

    def __repr__(self):
        return repr(self.text)


class Element:
    def __init__(self, tag, attributes, parent):
        self.tag = tag
        self.attributes = attributes
        self.children = []
        self.parent = parent

    def __repr__(self):
        return "<" + self.tag + ">"


def print_tree(node, indent=0):
    print(" " * indent, node)
    for child in node.children:
        print_tree(child, indent + 2)


def paint_tree(layout_object, display_list):
    display_list.extend(layout_object.paint())
    for child in layout_object.children:
        paint_tree(child, display_list)


def tree_to_list(tree, list):
    list.append(tree)
    for child in tree.children:
        tree_to_list(child, list)
    return list


class HTMLParser:
    SELF_CLOSING_TAGS = [
        "area",
        "base",
        "br",
        "col",
        "embed",
        "hr",
        "img",
        "input",
        "link",
        "meta",
        "param",
        "source",
        "track",
        "wbr",
    ]
    HEAD_TAGS = [
        "base",
        "basefont",
        "bgsound",
        "noscript",
        "link",
        "meta",
        "title",
        "style",
        "script",
    ]

    def __init__(self, body):
        self.body = body
        self.unfinished = []

    def add_text(self, text):
        if text.isspace():
            return
        self.implicit_tags(None)
        parent = self.unfinished[-1]
        node = Text(text, parent)
        parent.children.append(node)

    def add_tag(self, tag):
        tag, attributes = self.get_attributes(tag)
        if tag.startswith("!"):
            return
        self.implicit_tags(tag)
        # 終了タグの場合
        if tag.startswith("/"):
            if len(self.unfinished) == 1:
                return
            node = self.unfinished.pop()
            parent = self.unfinished[-1]
            parent.children.append(node)
        # 自己終了タグの場合、Elementとして親要素の子要素にする
        elif tag in self.SELF_CLOSING_TAGS:
            parent = self.unfinished[-1]
            node = Element(tag, attributes, parent)
            parent.children.append(node)
        # 開始タグの場合
        else:
            parent = self.unfinished[-1] if self.unfinished else None
            node = Element(tag, attributes, parent)
            self.unfinished.append(node)

    def get_attributes(self, text):
        parts = text.split()
        tag = parts[0].casefold()
        attributes = {}
        for attrpair in parts[1:]:
            if "=" in attrpair:
                key, value = attrpair.split("=", 1)
                if len(value) > 2 and value[0] in ["'", '"']:
                    value = value[1:-1]
                attributes[key.casefold()] = value
            else:
                attributes[attrpair.casefold()] = ""
        return tag, attributes

    def implicit_tags(self, tag):
        while True:
            open_tags = [node.tag for node in self.unfinished]
            if open_tags == [] and tag != "html":
                self.add_tag("html")
            elif open_tags == ["html"] and tag not in ["head", "body", "/html"]:
                if tag in self.HEAD_TAGS:
                    self.add_tag("head")
                else:
                    self.add_tag("body")
            elif (
                open_tags == ["html", "head"] and tag not in ["/head"] + self.HEAD_TAGS
            ):
                self.add_tag("/head")
            else:
                break

    def finish(self):
        if not self.unfinished:
            self.implicit_tags(None)
        while len(self.unfinished) > 1:
            node = self.unfinished.pop()
            parent = self.unfinished[-1]
            parent.children.append(node)
        return self.unfinished.pop()

    def parse(self):
        text = ""
        in_tag = False
        for c in self.body:
            if c == "<":
                in_tag = True
                if text:
                    self.add_text(text)
                text = ""
            elif c == ">":
                in_tag = False
                self.add_tag(text)
                text = ""
            else:
                text += c
        if not in_tag and text:
            self.add_text(text)
        return self.finish()


def cascade_priority(rule):
    selector, body = rule
    return selector.priority


class TagSelector:
    def __init__(self, tag):
        self.tag = tag
        self.priority = 1

    def matches(self, node):
        return isinstance(node, Element) and self.tag == node.tag


class DescendantSelector:
    def __init__(self, ancestor, descendant):
        self.ancestor = ancestor
        self.descendant = descendant
        self.priority = ancestor.priority + descendant.priority

    def matches(self, node):
        # 自分自身がdescendantのセレクタと一致するか
        # `p a`のaか？
        if not self.descendant.matches(node):
            return False
        while node.parent:
            # aの親を再帰的にたどり、親に`p`があれば一致
            if self.ancestor.matches(node.parent):
                return True
            node = node.parent
        return False


class CSSParser:
    def __init__(self, s):
        self.s = s
        self.i = 0

    def whitespace(self):
        # 空白の場合はiをインクリメントする
        while self.i < len(self.s) and self.s[self.i].isspace():
            self.i += 1

    def word(self):
        start = self.i
        while self.i < len(self.s):
            # プロパティ名として許容されてている文字である場合はiを進める
            if self.s[self.i].isalnum() or self.s[self.i] in "#-.%":
                self.i += 1
            # そうでなければループを抜ける
            else:
                break
        if not (self.i > start):
            raise Exception("Parsing error")
        return self.s[start : self.i]

    def literal(self, literal):
        if not (self.i < len(self.s) and self.s[self.i] == literal):
            raise Exception("Parsing error")
        self.i += 1

    def pair(self):
        prop = self.word()  # プロパティ
        self.whitespace()  # 空白
        self.literal(":")  # コロン
        self.whitespace()  # 空白
        val = self.word()  # 値
        return prop.casefold(), val

    def body(self):
        pairs = {}
        while self.i < len(self.s):
            try:
                prop, val = self.pair()  # プロパティと値のペア
                pairs[prop.casefold()] = val
                self.whitespace()  # 空白
                self.literal(";")  # 区切りのセミコロン
                self.whitespace()  # 空白
            except Exception:
                why = self.ignore_until([";", "}"])
                if why == ";":
                    self.literal(";")
                    self.whitespace()
                else:
                    break
        return pairs

    def ignore_until(self, chars):
        while self.i < len(self.s):
            if self.s[self.i] in chars:
                return self.s[self.i]
            else:
                self.i += 1
        return None

    def selector(self):
        out = TagSelector(self.word().casefold())
        self.whitespace()
        while self.i < len(self.s) and self.s[self.i] != "{":
            tag = self.word()
            descendant = TagSelector(tag.casefold())
            out = DescendantSelector(out, descendant)
            self.whitespace()
        return out

    def parse(self):
        rules = []
        while self.i < len(self.s):
            try:
                self.whitespace()  # 空白
                selector = self.selector()  # セレクタ
                self.literal("{")  # {
                self.whitespace()  # 空白
                body = self.body()  # ボディ
                self.literal("}")  # }
                rules.append((selector, body))
            except Exception:
                why = self.ignore_until(["}"])
                if why == "}":
                    self.literal("}")
                    self.whitespace()
                else:
                    break
        return rules


def style(node, rules):
    node.style = {}
    for property, default_value in INHERITED_PROPERTIES.items():
        if node.parent:
            node.style[property] = node.parent.style[property]
        else:
            node.style[property] = default_value
    for selector, body in rules:
        if not selector.matches(node):
            continue
        for property, value in body.items():
            node.style[property] = value
    if isinstance(node, Element) and "style" in node.attributes:
        pairs = CSSParser(node.attributes["style"]).body()
        for property, value in pairs.items():
            node.style[property] = value
    if node.style["font-size"].endswith("%"):
        if node.parent:
            parent_font_size = node.parent.style["font-size"]
        # ルートのhtml要素のとき(node.parentがないとき)
        else:
            parent_font_size = INHERITED_PROPERTIES["font-size"]
        node_pct = float(node.style["font-size"][:-1]) / 100
        parent_px = float(parent_font_size[:-2])
        node.style["font-size"] = str(node_pct * parent_px) + "px"
    for child in node.children:
        style(child, rules)


class DocumentLayout:
    def __init__(self, node):
        self.node = node
        self.parent = None
        self.children = []

    def layout(self):
        child = BlockLayout(self.node, self, None)
        self.children.append(child)
        self.display_list = child.display_list
        self.width = WIDTH - 2 * HSTEP
        self.x = HSTEP
        self.y = VSTEP
        child.layout()
        self.height = child.height

    def paint(self):
        return []


class BlockLayout:
    def __init__(self, node, parent, previous):
        self.node = node
        self.parent = parent
        self.previous = previous
        self.children = []
        self.display_list = []
        self.x = None
        self.y = None
        self.width = None
        self.height = None
        self.cursor_x = 0
        self.cursor_y = 0

    def layout_mode(self):
        if isinstance(self.node, Text):
            return "inline"
        elif any(
            [
                isinstance(child, Element) and child.tag in BLOCK_ELEMENTS
                for child in self.node.children
            ]
        ):
            return "block"
        elif self.node.children:
            return "inline"
        else:
            return "block"

    def layout(self):
        self.x = self.parent.x
        self.width = self.parent.width
        if self.previous:
            self.y = self.previous.y + self.previous.height
        else:
            self.y = self.parent.y
        mode = self.layout_mode()
        if mode == "block":
            previous = None
            for child in self.node.children:
                next = BlockLayout(child, self, previous)
                self.children.append(next)
                previous = next
        else:
            self.cursor_x = 0
            self.cursor_y = 0
            self.line = []
            self.recurse(self.node)
            self.flush()
        for child in self.children:
            child.layout()
        if mode == "block":
            self.height = sum([child.height for child in self.children])
        else:
            self.height = self.cursor_y

    def flush(self):
        if not self.line:
            return  # 行が空なら何もしない
        # 行内の最大アセントを計算
        max_ascent = max([font.metrics("ascent") for x, word, font, color in self.line])
        # ベースラインのy座標を計算 (レディングを考慮)
        baseline = self.cursor_y + 1.25 * max_ascent
        for rel_x, word, font, color in self.line:
            x = self.x + rel_x
            y = self.y + baseline - font.metrics("ascent")
            self.display_list.append((x, y, word, font, color))
        # 行内の最大ディセントを計算
        metrics = [font.metrics() for x, word, font, color in self.line]
        max_descent = max([metric["descent"] for metric in metrics])
        # 次の行のy座標を更新 (レディングを考慮)
        self.cursor_y = baseline + 1.25 * max_descent
        # xカーソルをリセットし、行バッファをクリア
        self.cursor_x = 0
        self.line = []

    def word(self, node, word):
        color = node.style["color"]
        weight = node.style["font-weight"]
        style = node.style["font-style"]
        if style == "normal":
            style = "roman"
        size = int(float(node.style["font-size"][:-2]) * 0.75)
        font = get_font(size, weight, style)
        w = font.measure(word)  # 単語の幅を測定
        if self.cursor_x + w > self.width:
            self.flush()
        self.line.append((self.cursor_x, word, font, color))
        # カーソルを単語の幅とスペース分だけ進める
        self.cursor_x += w + font.measure(" ")

    def recurse(self, node):
        if isinstance(node, Text):
            for word in node.text.split():
                self.word(node, word)
        else:
            if node.tag == "br":
                self.flush()
            for child in node.children:
                self.recurse(child)
        return self.display_list

    def paint(self):
        cmds = []
        if self.layout_mode() == "inline":
            for x, y, word, font, color in self.display_list:
                cmds.append(DrawText(self.x + x, self.y + y, word, font, color))
        if isinstance(self.node, Element) and self.node.tag == "pre":
            x2, y2 = self.x + self.width, self.y + self.height
            rect = DrawRect(self.x, self.y, x2, y2, "gray")
            cmds.append(rect)
        bgcolor = self.node.style.get("background-color", "transparent")
        if bgcolor != "transparent":
            x2, y2 = self.x + self.width, self.y + self.height
            rect = DrawRect(self.x, self.y, x2, y2, bgcolor)
            cmds.append(rect)
        return cmds


DEFAULT_STYLE_SHEET = CSSParser(open("browser.css").read()).parse()


class Browser:
    def __init__(self):
        self.window = tkinter.Tk()
        self.canvas = tkinter.Canvas(
            self.window, width=WIDTH, height=HEIGHT, bg="white"
        )
        self.canvas.pack()
        # スクロール位置を初期化
        self.scroll = 0
        # 下矢印キーにscrolldownメソッドをバインド
        self.window.bind("<Down>", self.scrolldown)

    def scrolldown(self, e):
        max_y = max(self.document.height + 2 * VSTEP - HEIGHT, 0)
        self.scroll = min(self.scroll + SCROLL_STEP, max_y)
        self.draw()

    # URLからWebページを読み込み、表示する関数
    def load(self, url):
        body = url.request()
        self.nodes = HTMLParser(body).parse()
        rules = DEFAULT_STYLE_SHEET.copy()
        links = [
            node.attributes["href"]
            for node in tree_to_list(self.nodes, [])
            if isinstance(node, Element)
            and node.tag == "link"
            and node.attributes.get("rel") == "stylesheet"
            and "href" in node.attributes
        ]
        for link in links:
            style_url = url.resolve(link)
            try:
                body = style_url.request()
            except:
                continue
            rules.extend(CSSParser(body).parse())
        style(self.nodes, sorted(rules, key=cascade_priority))
        self.document = DocumentLayout(self.nodes)
        self.document.layout()
        self.display_list = []
        paint_tree(self.document, self.display_list)
        self.draw()

    def draw(self):
        self.canvas.delete("all")
        for cmd in self.display_list:
            # スクロール量がcmdのtopに達してなければスキップ
            if cmd.top > self.scroll + HEIGHT:
                continue
            # スクロール量がcmdのbottomよりも大きければ見えないのでスキップ
            if cmd.bottom < self.scroll:
                continue
            cmd.execute(self.scroll, self.canvas)


if __name__ == "__main__":
    import sys

    # コマンドライン引数からURLを取得して読み込みます
    Browser().load(URL(sys.argv[1]))
    tkinter.mainloop()

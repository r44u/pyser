import socket
import ssl
import tkinter
import tkinter.font
from typing import Literal

HSTEP, VSTEP = 13, 18
WIDTH, HEIGTH = 800, 600
SCROLL_STEP = 100
FONTS = {}


def get_font(size, weight, style):
    key = (size, weight, style)
    if key not in FONTS:
        font = tkinter.font.Font(size=size, weight=weight, slant=style)
        label = tkinter.Label(font=font)
        FONTS[key] = (font, label)
    return FONTS[key][0]


class Text:
    def __init__(self, text, parent):
        self.text = text
        self.children = []
        self.parent = parent


class Element:
    def __init__(self, tag, parent):
        self.tag = tag
        self.children = []
        self.parent = parent

class HTMLParser:
    def __init__(self, body):
        self.body = body
        self.unfinished = []
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
    def add_text(self, text):
        parent = self.unfinished[-1]
        node = Text(text, parent)
        parent.children.append(node)
    def add_tag(self, tag):
        # 終了タグの場合
        if tag.startswith("/"):
            if len(self.unfinished) == 1:
                return
            node = self.unfinished.pop()
            parent = self.unfinished[-1]
            parent.children.append(node)
            
        # 開始タグの場合
        else:
            parent = self.unfinished[-1] if self.unfinished else None
            if self.unfinished
            node = Element(tag, parent)
            self.unfinished.append(node)

    def finish(self):
        while len(self.unfinished) > 1:
            node = self.unfinished.pop()
            parent = self.unfinished[-1]
            parent.children.append(node)
        return self.unfinished.pop()


class Layout:
    def __init__(self, tokens):
        self.display_list = []
        self.cursor_x = HSTEP
        self.cursor_y = VSTEP
        self.weight: Literal["normal", "bold"] = "normal"
        self.style: Literal["roman", "italic"] = "roman"
        self.size = 12
        self.line = []
        for tok in tokens:
            self.token(tok)
        self.flush()

    def token(self, tok):
        if isinstance(tok, Text):
            # textトークンはwordメソッドで単語ごとに処理
            for word in tok.text.split():
                self.word(word)
        elif tok.tag == "i":
            self.style = "italic"
        elif tok.tag == "/i":
            self.style = "roman"
        elif tok.tag == "b":
            self.weight = "bold"
        elif tok.tag == "/b":
            self.weight = "normal"
        elif tok.tag == "small":
            self.sizes -= 2
        elif tok.tag == "/small":
            self.sizes += 2
        elif tok.tag == "big":
            self.sizes += 4
        elif tok.tag == "/big":
            self.sizes -= 4
        elif tok.tag == "br":
            self.flush()  # <br>タグで行をフラッシュ
        elif tok.tag == "/p":
            self.flush()  # </p>タグで行をフラッシュ
            self.cursor_y += VSTEP  # 段落間のスペースを追加
        return self.display_list

    def flush(self):
        if not self.line:
            return  # 行が空なら何もしない
        # 行内の最大アセントを計算
        max_ascent = max([font.metrics("ascent") for x, word, font in self.line])
        # ベースラインのy座標を計算 (レディングを考慮)
        baseline = self.cursor_y + 1.25 * max_ascent
        # 各単語をベースラインに合わせて配置し、ディスプレイリストdisplay listに追加
        for x, word, font in self.line:
            y = baseline - font.metrics(
                "ascent"
            )  # ベースラインからアセント分だけ上に配置
            self.display_list.append((x, y, word, font))
        # 行内の最大ディセントを計算
        metrics = [font.metrics() for x, word, font in self.line]
        max_descent = max([metric["descent"] for metric in metrics])
        # 次の行のy座標を更新 (レディングを考慮)
        self.cursor_y = baseline + 1.25 * max_descent
        # xカーソルをリセットし、行バッファをクリア
        self.cursor_x = HSTEP
        self.line = []

    def word(self, word):
        font = get_font(self.size, self.weight, self.style)
        w = font.measure(word)  # 単語の幅を測定
        if self.cursor_x + w > WIDTH - HSTEP:  # 単語が右端を超える場合は改行
            self.flush()
        # ディスプレイリストdisplay listに単語とその座標を追加
        self.line.append((self.cursor_x, word, font))
        # カーソルを単語の幅とスペース分だけ進める
        self.cursor_x += w + font.measure(" ")


class URL:
    def __init__(self, url):
        # スキームと残りのurlを分割します
        self.scheme, url = url.split("://", 1)
        assert self.scheme in ["http", "https"]
        if self.scheme == "http":
            self.port = 80
        elif self.scheme == "https":
            self.port = 443

        # urlにパス区切りの'/'がないなら追加
        if "/" not in url:
            url = url + "/"
        # ホストと残りのurl（パス)を分割します
        self.host, url = url.split("/", 1)
        # パスを'/'から始まるように設定します
        self.path = "/" + url

        if ":" in self.host:
            self.host, port = self.host.split(":", 1)
            self.port = int(port)

    def request(self):
        # tcp/ipソケットを作成します
        s = socket.socket(
            family=socket.AF_INET,
            type=socket.SOCK_STREAM,
            proto=socket.IPPROTO_TCP,
        )
        s.connect((self.host, self.port))

        if self.scheme == "https":
            ctx = ssl.create_default_context()
            s = ctx.wrap_socket(s, server_hostname=self.host)

        # getリクエスト文字列を作成
        request = "GET {} HTTP/1.0\r\n".format(self.path)
        request += "HOST: {}\r\n".format(self.host)
        request += "\r\n"
        s.send(request.encode("utf8"))
        response = s.makefile("r", encoding="utf8", newline="\r\n")
        statusline = response.readline()
        version, status, explanation = statusline.split(" ", 2)
        response_headers = {}
        while True:
            line = response.readline()
            if line == "\r\n":
                break
            header, value = line.split(":", 1)
            response_headers[header.casefold()] = value.strip()

        # Transfer-Encodingヘッダがないことを確認
        assert "transfer-encoding" not in response_headers
        assert "content-encoding" not in response_headers
        content = response.read()
        s.close()
        return content


def show(body):
    in_tag = False
    for c in body:
        if c == "<":
            in_tag = True
        elif c == ">":
            in_tag = False
        elif not in_tag:
            # タグの外の文字を出力
            print(c, end="")


def lex(body):
    out = []
    buffer = ""
    in_tag = False
    for c in body:
        if c == "<":
            in_tag = True
            # バッファにテキストがあればTextオブジェクトとして追加
            if buffer:
                out.append(Text(buffer))
            buffer = ""  # バッファをクリア
        elif c == ">":
            in_tag = False
            out.append(Tag(buffer))
            buffer = ""
        elif not in_tag:
            buffer += c
    if not in_tag and buffer:
        out.append(Text(buffer))
    return out


def load(url):
    body = url.request()
    show(body)


class Browser:
    def __init__(self):
        self.window = tkinter.Tk()
        self.canvas = tkinter.Canvas(self.window, width=WIDTH, height=HEIGTH)
        self.canvas.pack()
        self.scroll = 0
        self.window.bind("<Down>", self.scrolldown)

    def load(self, url):
        body = url.request()
        tokens = lex(body)
        self.display_list = Layout(tokens).display_list
        # print(self.display_list)
        self.draw()

    def draw(self):
        self.canvas.delete("all")
        for x, y, c, font in self.display_list:
            if y > self.scroll + HEIGTH:
                continue
            if y + VSTEP < self.scroll:
                continue
            self.canvas.create_text(x, y - self.scroll, text=c, font=font, anchor="nw")

    def scrolldown(self, e):
        self.scroll += SCROLL_STEP
        self.draw()  # 再描画


if __name__ == "__main__":
    import sys

    Browser().load(URL(sys.argv[1]))
    tkinter.mainloop()

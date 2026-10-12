import socket
import urllib.parse
import random
import html


SESSIONS = {}
LOGINS = {"crashoverride": "0cool", "cerealkiller": "emmanuel", "": ""}
ENTRIES = [
    ("No names. We are nameless!", "cerealkiller"),
    ("HACK THE PLANET!!!", "crashoverride"),
]


def do_request(session, method, url, headers, body):
    if method == "GET" and url == "/":
        return "200 OK", show_comments(session)
    elif method == "GET" and url == "/count":
        return "200 OK", show_count()
    elif method == "GET" and url == "/animate":
        return "200 OK", show_animate()
    elif method == "GET" and url == "/animate.js":
        return "200 OK", show_animate_js()
    elif method == "GET" and url == "/eventloop.js":
        with open("eventloop.js") as f:
            return "200 OK", f.read()
    elif method == "GET" and url == "/trans":
        return "200 OK", show_transparent_example()
    elif method == "GET" and url == "/clip":
        return "200 OK", clip_mask_example()
    elif method == "GET" and url == "/css-transition":
        return "200 OK", show_css_transition()
    elif method == "GET" and url == "/example13-opacity-transition.css":
        return "200 OK", show_css_transition_css()
    elif method == "GET" and url == "/example13-opacity-transition.js":
        return "200 OK", show_css_transition_js()
    elif method == "GET" and url == "/overlapping":
        return "200 OK", show_overlapping_divs()
    elif method == "GET" and url == "/lorem":
        return "200 OK", show_lorem()
    elif method == "GET" and url == "/dark":
        return "200 OK", show_dark_mode_example()
    elif method == "GET" and url == "/example14-focus.css":
        return "200 OK", show_dark_mode_example_css()
    elif method == "GET" and url == "/alert":
        return "200 OK", show_alert()
    elif method == "GET" and url == "/example14-alert-role.js":
        return "200 OK", show_alert_js()
    elif method == "POST" and url == "/":
        params = form_decode(body)
        return do_login(session, params)
    elif method == "GET" and url == "/comment.js":
        with open("comment.js") as f:
            return "200 OK", f.read()
    elif method == "GET" and url == "/comment.css":
        with open("comment.css") as f:
            return "200 OK", f.read()
    elif method == "GET" and url == "/login":
        return "200 OK", login_form(session)
    elif method == "POST" and url == "/add":
        params = form_decode(body)
        add_entry(session, params)
        return "200 OK", show_comments(session)
    else:
        return "404 Not Found", not_found(url, method)


def show_count():
    out = "<!doctype html>"
    out += "<div>"
    out += " Let's count up to 99!"
    out += "</div>"
    out += "<div>Output</div>"
    out += "<script src=/eventloop.js></script>"
    return out


def show_animate():
    return """
    <div>This text fades</div>
    <script src=/animate.js></script>
    """


def show_animate_js():
    return """
var div = document.querySelectorAll("div")[0];
var total_frames = 120;
var current_frame = 0;
var change_per_frame = (0.999 - 0.1) / total_frames;
function animate() {
    current_frame++;
    var new_opacity = current_frame * change_per_frame + 0.1;
    div.style = "opacity:" + new_opacity;
    return current_frame < total_frames;
}
function run_animation_frame() {
    if (animate())
        requestAnimationFrame(run_animation_frame);
}
requestAnimationFrame(run_animation_frame);
    """


def do_login(session, params):
    username = params.get("username")
    password = params.get("password")
    if username in LOGINS and LOGINS[username] == password:
        session["user"] = username
        return "200 OK", show_comments(session)
    else:
        out = "<!doctype html>"
        out += "<h1>Invalid password for {}</h1>".format(username)
        return "401 Unauthorized", out


def show_css_transition():
    return """
<link rel=stylesheet href="example13-opacity-transition.css">
<button>Fade out</button>
<button>Fade in</button>
<div>This text fades</div>
<script src="example13-opacity-transition.js"></script>
    """


def show_css_transition_css():
    return """
div {
    opacity: 0.999;
    transition: opacity 2s;
}
"""


def show_css_transition_js():
    return """
var div = document.querySelectorAll("div")[0];

function start_fade_out(e) {
    div.style = "opacity:0.1";
    e.preventDefault();
}

function start_fade_in(e) {
    div.style = "opacity:0.999";
    e.preventDefault();
}
var buttons = document.querySelectorAll("button");
buttons[0].addEventListener("click", start_fade_out);
buttons[1].addEventListener("click", start_fade_in);
"""


def show_overlapping_divs():
    return """
<div style="opacity:0.8">
  <div></div>
  <div style="overflow:clip;border-radius:30px;opacity:0.5;background-color:lightblue;transform:translate(50px,10px)">Underneath</div>
  <div style="background-color:lightgreen;transform:translate(0px,0px)">On top</div>
</div>
    """


def show_lorem():
    return """
<div>Lorem ipsum dolor sit amet,consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.</div>
"""


def show_dark_mode_example():
    return """
<link rel=stylesheet href="example14-focus.css">
<button tabindex=2>This is a button</button>
<br>
This is an input element: <input> and
<a tabindex=1 href="/">this is a link.</a>
<div>Not focusable</div>
<div role=textbox>custom contents</div>
<div tabindex=3>Tabbable element</div>
<script src="example14-focus.js"></script>
<br> . <br> . <br> . <br> . <br> . <br> .
<br> . <br> . <br> . <br> . <br> . <br> .
<br> . <br> . <br> . <br> . <br> . <br> .
<div tabindex=12>Offscreen</div>
<a href="http://browser.engineering">browser.engineering</a>
"""


def show_dark_mode_example_css():
    return """
@media (prefers-color-scheme: dark) {
  a { color: lightblue; }
  input { background-color: #2222FF; }
  button { background-color: #992500; }
}
"""


def show_alert():
    return """
<div>Alert text</div>
<button>Toggle alert role</button>
<script src="example14-alert-role.js"></script>
"""


def show_alert_js():
    return """
div = document.querySelectorAll("div")[0]
button = document.querySelectorAll("button")[0]
button.addEventListener("click", onclick);
function onclick(e) {
	if (!div.getAttribute("role"))
		div.setAttribute("role", "alert");
	else
		div.setAttribute("role", "");
	e.preventDefault();
}
"""


def show_comments(session):
    out = "<!doctype html>"
    out += "<link rel=stylesheet href=/comment.css>"
    out += "<script src=https://example.com/evil.js></script>"
    for entry, who in ENTRIES:
        out += "<p>" + html.escape(entry) + "\n"
        out += "<i>by " + html.escape(who) + "</i></p>"

    if "user" in session:
        nonce = str(random.random())[2:]
        session["nonce"] = nonce
        out += "<script src=/comment.js></script>"
        out += "<h1>Hello, " + session["user"] + "</h1>"
        out += "<form action=add method=post>"
        out += "<input name=nonce type=hidden value=" + nonce + ">"
        out += "<p><input name=guest></p>"
        out += "<p><button>Sign the book!</button></p>"
        out += "</form>"
    else:
        out += "<a href=/login>Sign in to write in the guest book</a>"
    return out


def show_transparent_example():
    return """
    <!doctype html>
    <div style="background-color:orange">
        Parent
        <div style="background-color:blue;mix-blend-mode:difference">
            Child
        </div>
        Parent
    </div>
    """


def clip_mask_example():
    return """
    <!doctype html>
    <div
      style="border-radius:30px;background-color:lightblue;overflow:clip">
        This test text exists here to ensure that the "div" element is
        large enough that the border radius is obvious.
    </div>
    """


def login_form(session):
    body = "<!doctype html>"
    body += "<form action=/ method=post>"
    body += "<p>Username: <input name=username></p>"
    body += "<p>Password: <input name=password type=password></p>"
    body += "<p><button>Log in</button></p>"
    body += "</form>"
    return body


def form_decode(body):
    params = {}
    for field in body.split("&"):
        name, value = field.split("=", 1)
        name = urllib.parse.unquote_plus(name)
        value = urllib.parse.unquote_plus(value)
        params[name] = value
    return params


def not_found(url, method):
    out = "<!doctype html>"
    out += "<h1>{} {} not found!</h1>".format(method, url)
    return out


def add_entry(session, params):
    if "nonce" not in session or "nonce" not in params:
        return
    if session["nonce"] != params["nonce"]:
        return
    if "user" not in session:
        return
    if "guest" in params and len(params["guest"]) <= 100:
        ENTRIES.append((params["guest"], session["user"]))
    return show_comments(session)


def handle_connection(conx):
    req = conx.makefile("b")
    reqline = req.readline().decode("utf8")
    method, url, version = reqline.split(" ", 2)
    assert method in ["GET", "POST"]
    headers = {}
    while True:
        line = req.readline().decode("utf8")
        if line == "\r\n":
            break
        header, value = line.split(":", 1)
        headers[header.casefold()] = value.strip()
    if "content-length" in headers:
        length = int(headers["content-length"])
        body = req.read(length).decode("utf8")
    else:
        body = None
    if "cookie" in headers:
        token = headers["cookie"][len("token=") :]
    else:
        token = str(random.random())[2:]
    session = SESSIONS.setdefault(token, {})
    status, body = do_request(session, method, url, headers, body)
    response = "HTTP/1.0 {}\r\n".format(status)
    response += "Content-Length: {}\r\n".format(len(body.encode("utf8")))
    if "cookie" not in headers:
        template = "Set-Cookie: token={}; SameSite=Lax\r\n"
        response += template.format(token)
    csp = "default-src http://localhost:8000 http://host.docker.internal:8000"
    response += "Content-Security-Policy: {}\r\n".format(csp)
    response += "\r\n" + body
    conx.send(response.encode("utf8"))
    conx.close()


s = socket.socket(
    family=socket.AF_INET, type=socket.SOCK_STREAM, proto=socket.IPPROTO_TCP
)
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

s.bind(("", 8000))
s.listen()

while True:
    conx, addr = s.accept()
    handle_connection(conx)

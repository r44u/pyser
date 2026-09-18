console = { log: function (x) { call_python("log", x); } }

document = {
  querySelectorAll: function (s) {
    var handles = call_python("querySelectorAll", s);
    return handles.map(function (h) { return new Node(h) });
  }
}

LISTENERS = {}

function Node(handle) {
  this.handle = handle;
}

Node.prototype.getAttribute = function (attr) {
  return call_python("getAttribute", this.handle, attr)
}

Node.prototype.addEventListener = function (type, listener) {
  if (!LISTENERS[this.handle]) LISTENERS[this.handle] = {}
  var dict = LISTENERS[this.handle];
  if (!dict[type]) dict[type] = [];
  var list = dict[type];
  list.push(listener);
}

function Event(type) {
  this.type = type;
  this.do_default = true;
}
Event.prototype.preventDefault = function () {
  this.do_default = false;
}
Node.prototype.dispatchEvent = function (evt) {
  var type = evt.type;
  var list = (LISTENERS[this.handle] && LISTENERS[this.handle][type]) || [];
  for (var i = 0; i < list.length; i++) {
    list[i].call(this, evt);
  }
  return evt.do_default;
}

RAF_LISTENERS = [];
function requestAnimationFrame(fn) {
  RAF_LISTENERS.push(fn);
  call_python("requestAnimationFrame");
}

function __runRAFHandlers() {
  var handlers_copy = RAF_LISTENERS;
  RAF_LISTENERS = [];
  for (var i = 0; i < handlers_copy.length; i++) {
    handlers_copy[i]();
  }
}

SET_TIMEOUT_REQUESTS = {}
function setTimeout(callback, time_delta) {
  var handle = Object.keys(SET_TIMEOUT_REQUESTS).length;
  SET_TIMEOUT_REQUESTS[handle] = callback;
  call_python("setTimeout", handle, time_delta);
}

function __runSetTimeout(handle) {
  var callback = SET_TIMEOUT_REQUESTS[handle];
  callback();
}

function __runXHROnload(body, handle) {
  var obj = XHR_REQUESTS[handle];
  var event = new Event('load');
  obj.responseText = body;
  if (obj.onload) obj.onload(event);
}

XHR_REQUESTS = {}

function XMLHttpRequest() {
  this.handle = Object.keys(XHR_REQUESTS).length;
  XHR_REQUESTS[this.handle] = this;
}

XMLHttpRequest.prototype.open = function (method, url, is_async) {
  this.is_async = is_async;
  this.method = method;
  this.url = url;
}

XMLHttpRequest.prototype.send = function (body) {
  this.responseText = call_python("XMLHttpRequest_send", this.method, this.url, body, this.is_async, this.handle);
}


// この定義は一番下にしないと謎に落ちるから注意
Object.defineProperty(Node.prototype, 'innerHTML', {
  set: function (s) {
    call_python("innerHTML_set", this.handle, s.toString());
  }
});

Object.defineProperty(Node.prototype, 'style', {
  set: function (s) {
    call_python("style_set", this.handle, s.toString());
  }
});

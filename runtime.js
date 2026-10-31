window.console = { log: function (x) { call_python("log", x); } }

window.document = {
  querySelectorAll: function (s) {
    var handles = call_python("querySelectorAll", s, window._id);
    return handles.map(function (h) { return new window.Node(h) });
  }
}

window.Node = function Node(handle) { this.handle = handle; }

window.Node.prototype.getAttribute = function (attr) {
  return call_python("getAttribute", this.handle, attr, window._id);
}

window.LISTENERS = {}

window.Node.prototype.addEventListener = function (type, listener) {
  if (!window.LISTENERS[this.handle]) window.LISTENERS[this.handle] = {};
  var dict = window.LISTENERS[this.handle];
  if (!dict[type]) dict[type] = [];
  var list = dict[type];
  list.push(listener);
}

window.Event = function Event(type) {
  this.type = type
  this.do_default = true;
}
window.Event.prototype.preventDefault = function () {
  this.do_default = false;
}

window.Node.prototype.dispatchEvent = function (evt) {
  var type = evt.type;
  var list = (window.LISTENERS[this.handle] && window.LISTENERS[this.handle][type]) || [];
  for (var i = 0; i < list.length; i++) {
    list[i].call(this, evt);
  }
  return evt.do_default;
}

Object.defineProperty(window.Node.prototype, 'innerHTML', {
  set: function (s) {
    call_python("innerHTML_set", this.handle, s.toString(), window._id);
  }
});

window.XHR_REQUESTS = {}

window.XMLHttpRequest = function XMLHttpRequest() {
  this.handle = Object.keys(window.XHR_REQUESTS).length;
  window.XHR_REQUESTS[this.handle] = this;
}

window.XMLHttpRequest.prototype.open = function (method, url, is_async) {
  this.is_async = is_async;
  this.method = method;
  this.url = url;
}

window.XMLHttpRequest.prototype.send = function (body) {
  this.responseText = call_python("XMLHttpRequest_send",
    this.method, this.url, body, this.is_async, this.handle, window._id);
}

window.__runXHROnload = function __runXHROnload(body, handle) {
  var obj = window.XHR_REQUESTS[handle];
  var evt = new window.Event('load');
  obj.responseText = body;
  if (obj.onload)
    obj.onload(evt);
}

window.SET_TIMEOUT_REQUESTS = {}

window.setTimeout = function setTimeout(callback, time_delta) {
  var handle = Object.keys(window.SET_TIMEOUT_REQUESTS).length;
  window.SET_TIMEOUT_REQUESTS[handle] = callback;
  call_python("setTimeout", handle, time_delta, window._id)
}

window.__runSetTimeout = function __runSetTimeout(handle) {
  var callback = window.SET_TIMEOUT_REQUESTS[handle]
  callback();
}

window.RAF_LISTENERS = [];

window.requestAnimationFrame = function requestAnimationFrame(fn) {
  window.RAF_LISTENERS.push(fn);
  call_python("requestAnimationFrame", window._id);
}

window.__runRAFHandlers = function __runRAFHandlers() {
  var handlers_copy = window.RAF_LISTENERS;
  window.RAF_LISTENERS = [];
  for (var i = 0; i < handlers_copy.length; i++) {
    handlers_copy[i]();
  }
}

Object.defineProperty(window.Node.prototype, 'style', {
  set: function (s) {
    call_python("style_set", this.handle, s.toString(), window._id);
  }
});

window.Node.prototype.setAttribute = function (attr, value) {
  return call_python("setAttribute", this.handle, attr, value, window._id);
}

Object.defineProperty(Window.prototype, 'parent', {
  configurable: true,
  get: function () {
    var parent_id = call_python('parent', window._id);
    if (parent_id != undefined) {
      var parent = WINDOWS[parent_id];
      if (parent === undefined) parent = new Window(parent_id);
      return parent;
    }
  }
});

window.WINDOW_LISTENERS = {}

window.MessageEvent = function (data) {
  this.type = "message";
  this.data = data;
}

Window.prototype.addEventListener = function (type, listener) {
  if (!window.WINDOW_LISTENERS[this.handle]) window.WINDOW_LISTENERS[this.handle] = {};
  var dict = window.WINDOW_LISTENERS[this.handle];
  if (!dict[type]) dict[type] = [];
  var list = dict[type];
  list.push(listener);
}

Window.prototype.dispatchEvent = function (evt) {
  var type = evt.type;
  var list = (window.WINDOW_LISTENERS[this.handle] && window.WINDOW_LISTENERS[this.handle][type]) || [];
  for (var i = 0; i < list.length; i++) {
    list[i].call(this, evt);
    return evt.do_default;
  }
}
Window.prototype.postMessage = function (message, origin) {
  call_python("postMessage", this._id, message, origin)
}

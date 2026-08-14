console = { log: function (x) { call_python("log", x); } }

document = {
  querySelectorAll: function (s) {
    var handles = call_python("querySelectorAll", s);
    return handles.map(function (h) { return new Node(h) });
  }
}

function Node(handle) {
  this.handle = handle;
}

Node.prototype.getAttribute = function (attr) {
  return call_python("getAttribute", this.handle, attr)
}

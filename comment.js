var strong = document.querySelectorAll("strong")[0];

function lengthCheck() {
  var value = this.getAttribute("value")
  console.log(value.length, strong)
  if (value.length > 10) {
    strong.innerHTML = "comment too long!";
  }
}

var inputs = document.querySelectorAll("input");

for (var i = 0; i < inputs.length; i++) {
  inputs[i].addEventListener("keydown", lengthCheck);
}

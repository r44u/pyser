var count = 0;
function callback() {
  var output = document.querySelectorAll("div")[1];
  output.innerHTML = "count: " + (count++);
  console.log(output.innerHTML);
  if (count < 100)
    requestAnimationFrame(callback);
};
requestAnimationFrame(callback);

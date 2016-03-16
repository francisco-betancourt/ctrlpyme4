function instance(template, data) {
  var clone = document.importNode(template, true);

  for (var k in data) {
    console.log(k);
  }

  return clone;
}

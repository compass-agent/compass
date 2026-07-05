(function () {
  function applyHoverStyles() {
    var nodes = document.querySelectorAll('[style-hover]');
    nodes.forEach(function (node) {
      var base = node.getAttribute('style') || '';
      var hover = node.getAttribute('style-hover') || '';
      if (!hover) return;
      node.addEventListener('mouseenter', function () {
        node.setAttribute('style', base + ';' + hover);
      });
      node.addEventListener('mouseleave', function () {
        node.setAttribute('style', base);
      });
      node.addEventListener('focus', function () {
        node.setAttribute('style', base + ';' + hover);
      });
      node.addEventListener('blur', function () {
        node.setAttribute('style', base);
      });
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', applyHoverStyles);
  } else {
    applyHoverStyles();
  }
}());

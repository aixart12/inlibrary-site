// Small enhancements only — every page works without this file.
// 1. Close the phone menu after a link is tapped, on Escape, or on a tap outside it.
// 2. Open the "On this page" list on wide screens, where it sits in the sidebar.

(function () {
  var menu = document.querySelector('details.menu');
  if (menu) {
    menu.querySelectorAll('a').forEach(function (link) {
      link.addEventListener('click', function () {
        menu.open = false;
      });
    });
    document.addEventListener('keydown', function (event) {
      if (event.key === 'Escape' && menu.open) {
        menu.open = false;
        menu.querySelector('summary').focus();
      }
    });
    document.addEventListener('click', function (event) {
      if (menu.open && !menu.contains(event.target)) menu.open = false;
    });
  }

  var toc = document.querySelector('details.toc');
  if (toc && window.matchMedia) {
    var wide = window.matchMedia('(min-width: 1024px)');
    var sync = function () {
      toc.open = wide.matches;
    };
    sync();
    if (wide.addEventListener) wide.addEventListener('change', sync);
  }
})();

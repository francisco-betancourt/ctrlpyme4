(function () {
  var supert = document.querySelector('.supert');
  if (!supert) { return; }

  // search
  var search_form = document.getElementById('supert_search_form');
  if (search_form) {
    search_form.addEventListener('submit', function (event) {
      event.preventDefault();
      var s_term = document.getElementById('supert_search').value;
      var splited_url = window.location.href.split('?');
      var base_url = splited_url[0];
      var url_vars = splited_url[1];
      var new_vars = '';
      var re = /term=.*(?=&)|term=.*$/;
      if (url_vars) {
        url_vars = url_vars.replace('#', '');
        var vars = url_vars.split('&');
        var term_found = false;
        for (var i = 0; i < vars.length; i++) {
          if (!vars[i]) continue;
          new_vars += vars[i].replace(re, 'term=' + s_term);

          if (i < vars.length - 1) { new_vars += '&'; }
          term_found = vars[i].search(re) >= 0;
          if (term_found) { break }
        }
        if (!term_found) { new_vars += '&term=' + s_term; }
        url_vars = new_vars;
      } else {
        url_vars = 'term=' + s_term;
      }
      url_vars = url_vars.replace(/&page=.*(?=&)|&page=.*$/, '');
      window.location.href = base_url + '?' + url_vars;
    });
  }

  function getCheckedCbs() {
    var cbs = supert.querySelectorAll('input[type="checkbox"]:checked');
    return cbs;
  }
  function countChecked() {
    var n = getCheckedCbs().length;
    supert.querySelector('#supert_card_header');
  };
  var cb_master = document.getElementById('cb_master');
  if (cb_master) {
    var cbs = supert.querySelectorAll('input[type="checkbox"]:not(#cb_master)');
    for (var index = 0; index < cbs.length; index++) {
      var the_cb = cbs[index];
      the_cb.addEventListener('change', function (event) {
        countChecked();
      })
    }
    cb_master.addEventListener('change', function (event) {
      for (var index = 0; index < cbs.length; index++) {
        if (event.target.checked) {
          cbs[index]._change(true);
        } else {
          cbs[index]._change(false);
        }
      }
      countChecked();
    });
  }

})();

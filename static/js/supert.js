(function () {
  var supert = document.querySelector('.supert');
  if (!supert) { return; }

  // search
  var search_form = document.getElementById('supert_search_form');
  if (search_form) {
    search_form.addEventListener('submit', function (event) {
      event.preventDefault();
      // window.location.href = ''
    })
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

// The MIT License (MIT)
// Copyright (c) 2016 Daniel J. Ramirez
//
// Permission is hereby granted, free of charge, to any person obtaining a copy
// of this software and associated documentation files (the "Software"), to deal
// in the Software without restriction, including without limitation the rights
// to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
// copies of the Software, and to permit persons to whom the Software is
// furnished to do so, subject to the following conditions:
//
// The above copyright notice and this permission notice shall be included in all
// copies or substantial portions of the Software.
//
// THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
// IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
// FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
// AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
// LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
// OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
// SOFTWARE.

(function () {

  URL = (function() {
    var M = {
      vars: {}
    };

    var splited_url = window.location.href.split('?');
    var base_url = splited_url[0];
    if (base_url.slice(-1) == '#')
      base_url = base_url.slice(0, -1);

    var url_vars = splited_url[1];
    var new_vars = '';
    if (url_vars) {
      url_vars = url_vars.replace('#', '');
      var vars = url_vars.split('&');
      for (var i = 0; i < vars.length; i++) {
        if (!vars[i]) continue;
        var pair = vars[i].split('=');
        M.vars[pair[0]] = pair[1];
      }
    }

    M.generate_url = function() {
      var url = base_url;
      var vars_concat = '';
      for (var key in M.vars) {
        if (!M.vars[key]) continue;
        vars_concat += key + '=' + M.vars[key] + '&';
      }
      if (vars_concat) {
        vars_concat = vars_concat.slice(0, -1);
        url += '?' + vars_concat;
      }

      return url
    };

    return M;
  })();

  function settup_supert(supert) {
    if (!supert) { return; }
    var t_index = supert.dataset.index;

    // search
    var search_form = supert.querySelector('.st-search-form');
    if (search_form) {
      search_form.addEventListener('submit', function (event) {
        var term_str = "term_" + t_index;
        event.preventDefault();
        var s_term = supert.querySelector('.st-search-input').value;
        URL.vars[term_str] = s_term;
        window.location.href = URL.generate_url();
      });
    }


    var ipp_value = supert.querySelector('.ipp-value');
    var ipp_form = supert.querySelector('.st-ipp-form');

    ipp_value.addEventListener('click', function(event) {
      this.setAttribute('hidden', 'hidden');
      ipp_form.removeAttribute('hidden');
      var input = ipp_form.querySelector('.form-control');
      input.focus();
      input.setSelectionRange(0, input.value.length);
    });
    ipp_form.addEventListener('submit', function(event) {
      event.preventDefault();
      var new_ipp = ipp_form.querySelector('.form-control').value;
      URL.vars['ipp_' + t_index] = new_ipp;
      console.log(URL.generate_url());
      window.location.href = URL.generate_url();
    });
    ipp_form.addEventListener('focusout', function (event) {
      ipp_value.removeAttribute('hidden');
      this.setAttribute('hidden', 'hidden');
    });


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
  }

  var superts = document.querySelectorAll('.supert');
  for( var index = 0; index < superts.length; index++ ) {
      settup_supert(superts[index]);
  }


})();


$('#nav_screen')[0].addEventListener('transitionend', function (event) {
  if (event.target.style.opacity == 0) {
    $('#nav_screen').css('visibility', 'hidden');
  }
}, true);

function show_nav_screen() {
  $('#nav_screen').css('opacity', '1');
  $('#nav_screen').css('visibility', 'visible');
}
function hide_nav_screen() {
  $('#nav_screen').css('opacity', '0');
}

function hide_main_menu() {
  hide_container('main_menu_m', true);
  hide_container('m_nav_filler', true);
  hide_nav_screen();
}

function close_search() {
  $('#bag_btn, #search_menu_btn, .brand, #notifications_btn, #help_menu_btn').show();
  $('#hamburger, #search_menu_btn').removeClass('hidden');
  $('#close_search').css('display', 'none');
  $('.submenu').hide();
  $('#search_form').css('transform', 'translateY(-64px)');
  $('#search_form').css('width', '0px');
}

function toggle_main_menu() {
  if ($('#main_menu_m').attr('state') == 'hidden') {
    show_container('main_menu_m');
    show_container('m_nav_filler');
    show_nav_screen();
    // $('#nav_screen').show();
  } else {
    hide_main_menu();
  }
  close_search();
}

$('.hamburger').click(function (event) {
  toggle_main_menu();
});

$('#nav_screen, #bag_btn, #search_form').click(function (event) {
  $('.submenu').hide();
  hide_main_menu();
  hide_nav_screen();
})

function toggle_submenu(name) {
  $('.submenu').not('#submenu_' + name).hide();
  $('#submenu_' + name).toggle();
  if ($('#hamburger').css('display') == 'none' || $('#hamburger').css('display') == 'none !important' || name == 'auth') {
    if ($('#submenu_' + name).css('display') == 'block') {
      show_nav_screen();
    } else {
      hide_nav_screen();
    }
  }
}


$('#close_search').click(function (event) {
  close_search();
});

$('#search_menu_btn').click(function (event) {
  $('#bag_btn, #search_menu_btn, .brand, #notifications_btn, #help_menu_btn').hide();
  $('#hamburger, #search_menu_btn').addClass('hidden');
  $('#close_search').css('display', 'flex');
  $('.submenu').hide();
  hide_nav_screen();
  hide_main_menu();
  $('#search_form').css('transform', 'translateY(0px)');
  $('#search_form').css('width', '100%');
  $('#search').focus();
});


function show_help() {
  try {
    var help_window = window.open(HELP_WINDOW_URL, 1,  "width=500, height=600, resizable, scrollbars=yes, status=1");
  } catch (ex) {}
}

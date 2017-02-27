// dont forget to set item_id.
try {
  $('#categories_tree').treeview({
    data: categories_tree_data,
    checkedIcon: 'fa fa-check-square-o',
    uncheckedIcon: 'fa fa-square-o',
    expandIcon: 'fa fa-plus',
    collapseIcon: 'fa fa-minus',
    showCheckbox: true,
    highlightSelected: false,
    levels: 1
  });  
} catch (e) {}



var traits_map = {};
var traits_count = 0;


function fill_datalist(options, target) {
  $(target.list).empty();
  for (var index in options) {
    var option = options[index];
    var el_option = $('<option value="' + option.name + '">' + option.name + '</option>\n');
    $(target.list).append(el_option);
  }
}


function search_trait_category_names(target) {
  var val = $(target).val();
  $.ajax({
    url: AJAX_SEARCH_TRAIT_CATEGORIES_URL + '?term=' + val
  })
  .done(function(res) {
    var options = res.match;
    fill_datalist(options, target);
  })
  .fail(function(res) { });
}

function search_traits_by_category_name(target) {
  var cat_name = $('#new_trait_category_name').val();
  var val = $(target).val();
  $.ajax({
    url: AJAX_SEARCH_TRAITS_URL + '?category_name=' + cat_name + '&term=' + val
  })
  .done(function(res) {
    var options = res.match;
    fill_datalist(options, target);
  })
  .fail(function(res) { });
}


function avoid_event(event) {
  // avoid submit when pressing arrow keys
  return event.keyCode >= 37 && event.keyCode <= 40 || event.keyCode == 13;
}

$('.trait-category-name').keyup(function (event) {
  if (avoid_event(event)) return;
  search_trait_category_names(event.target);
});
$('.trait-category-name').on('focusin', function (event) {
  search_trait_category_names(event.target);
});


$('.trait-option').on('keyup', function (event) {
  if (avoid_event(event)) return;
  search_traits_by_category_name(event.target);
});
$('.trait-option').on('focusin', function (event) {
  search_traits_by_category_name(event.target);
});


$('.trait-category-name, .trait-option').on('focusout', function (event) {
  $(event.target.list).empty();
});


var proto_trait_li = document.getElementById('proto_trait_li');
function update_traits_list() {
  $('#current_traits').empty();
  var s = "";
  for (var k in traits_map) {
    var trait_option = traits_map[k];
    s += k + ':' + trait_option + ',';
    var new_trait = $(document.importNode(proto_trait_li.content, true));
    new_trait.find('.trait-name').text(k + ' : ');
    new_trait.find('.trait-option').text(trait_option);
    var remove_btn = new_trait.find('.remove-btn');
    remove_btn.attr('data-key', k);
    remove_btn.click(function (event) {
      var key = $(this).attr('data-key');
      delete traits_map[key];
      console.log(traits_map);
      $(this).parent().remove();
      update_selected_traits_input();
    });
    $('#current_traits').append(new_trait);
  }
  s = s.slice(0,-1);
  $('#traits_selected').val(s);
}

$('#new_trait_button').click(function (event) {
  event.preventDefault();
  var cat_name = $('#new_trait_category_name').val();
  var option = $('#new_trait_option').val();
  if (!option || !cat_name) return;
  traits_map[cat_name] = option;
  update_traits_list();
  $('#new_trait_category_name').val("");
  $('#new_trait_option').val("");
})


function update_selected_traits_input() {
  var s = "";
  for (var k in traits_map) {
    var trait_option = traits_map[k];
    s += k + ':' + trait_option + ',';
  }
  s = s.slice(0,-1);
  $('#traits_selected').val(s);
}


function update_traits_map_from_selected_traits() {
  var initial_selected = $('#traits_selected').val();
  if (!initial_selected) return;

  var subs = initial_selected.split(',');
  for (var index in subs) {
    var kv = subs[index].split(':')
    cat_name = kv[0]
    option = kv[1]
    traits_map[cat_name] = option;
  }
  update_traits_list();
}

update_traits_map_from_selected_traits();



// set initial traits
$('#categories_tree').bind('nodeChecked nodeUnchecked', function(event, node) {
  // select parent categories
  var currentNode = node;
  while (currentNode.parentId >= 0) {
    parent = $('#categories_tree').treeview('getParent', currentNode);
    if (event.type == 'nodeChecked') {
      $('#categories_tree').treeview('checkNode', [ parent, { silent: true } ]);
      currentNode = parent;
    }
    else {
      $('#categories_tree').treeview('uncheckNode', [ parent, { silent: true } ]);
      currentNode = parent;
    }
  }

  var selected = $('#categories_tree').treeview('getChecked');
  var selected_categories = "";
  for(var i = 0; i < selected.length; i++) {
    selected_categories += selected[i].category_id;
    if (i < selected.length - 1) {
      selected_categories += ',';
    }
  }
  $('#categories_selected').attr('value', selected_categories);
});



$('#category_search').bind('change paste keyup', function(event) {
  var pattern = $(this).val()
  $('#categories_tree').treeview('collapseAll', { silent: true });
  $('#categories_tree').treeview('search', [pattern , {
    ignoreCase: true,     // case insensitive
    exactMatch: false,    // like or equals
    revealResults: true  // reveal matching nodes
  }]);
});

$("#item_is_bundle").on('click', function(event) {
  if (event.target.checked) {
    $("#bundle_items_form_group").show();
  }
  else {
    $("#bundle_items_form_group").hide();
  }
});

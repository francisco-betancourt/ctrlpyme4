// dont forget to set item_id.
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


function fill_datalist(options, target) {
  $(target.list).empty();
  target.list.style.display = 'block';

  for (var index in options) {
    var option = options[index];
    var el_option = $('<option value="' + option.name + '">' + option.name + '</option>\n');
    $(target.list).append(el_option);
  }
}


function search_trait_category_names(target) {
  var val = $(target).val();
  $.ajax({
    url: AJAX_SEARCH_TRAIT_CATEGORIES_URL + '/' + val
  })
  .done(function(res) {
    var options = res.match;
    fill_datalist(options, target);
  })
  .fail(function(res){

  })
}

function search_traits_by_category_name(target) {
  var cat_name = $('#new_trait_category_name' + target.dataset.suffix).val();
  var val = $(target).val();
  $.ajax({
    url: AJAX_SEARCH_TRAITS_URL + '/' + cat_name + '/' + val
  })
  .done(function(res) {
    var options = res.match;
    fill_datalist(options, target);
  })
  .fail(function(res){

  })
}


$('.trait-category-name').keyup(function (event) {
  search_trait_category_names(event.target);
});
$('.trait-category-name').on('focusin', function (event) {
  search_trait_category_names(event.target);
});


$('.trait-option').on('keyup', function (event) {
  search_traits_by_category_name(event.target);
});
$('.trait-option').on('focusin', function (event) {
  search_traits_by_category_name(event.target);
});


$('.trait-category-name, .trait-option').on('focusout', function (event) {
  $(event.target.list).empty();
  event.target.list.style.display = 'none';
});


function update_categories_and_traits() {
  var selected_categories = $('#categories_selected').val();
  $.ajax({
    url: "/ctrlpyme4/item/trait_selector_data.json/" + item_id + "?categories=" + selected_categories
  })
  .done(function(data) {
    // create the traits tree.
    if (data.status == "no traits") {
      $('#traits_tree *').remove();
      return;
    }
    $('#traits_tree').treeview({
      data: data.traits,
      multiSelect: true,
      selectedIcon: 'fa fa-check',
      expandIcon: 'fa fa-plus',
      collapseIcon: 'fa fa-minus',
      highlightSelected: false,
      levels: 1
    });

    $('#traits_tree').bind('nodeSelected nodeUnselected', function(event, node) {
      var siblings = $('#traits_tree').treeview('getSiblings', node);
      var selected_traits = "";
      for(var i = 0; i < siblings.length; i++) {
        $('#traits_tree').treeview('unselectNode', [ siblings[i], { silent: true } ]);
      }
      var selected = $('#traits_tree').treeview('getSelected');
      var selected_traits = "";
      for(var i = 0; i < selected.length; i++) {
        selected_traits += selected[i].trait_id;
        if (i < selected.length - 1) {
          selected_traits += ',';
        }
      }
      $('#traits_selected').prop('value', selected_traits);
    });

  })
  .fail(function(data) {
    console.log(data);
  });
}

update_categories_and_traits();
try {
  $('#traits_selected').prop('value', initial_selected_traits);
} catch (ex) {
  console.log('initial_traits_selected not defined');
}



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
  update_categories_and_traits();
});



$('#category_search').bind('change paste keyup', function(event) {
  var pattern = $(this).val()
  $('#categories_tree').treeview('collapseAll', { silent: true });
  $('#categories_tree').treeview('search', [pattern , {
    ignoreCase: true,     // case insensitive
    exactMatch: false,    // like or equals
    revealResults: true  // reveal matching nodes
  }]);
})

$("#item_is_bundle").on('click', function(event) {
  if (event.target.checked) {
    $("#bundle_items_form_group").show();
  }
  else {
    $("#bundle_items_form_group").hide();
  }
});

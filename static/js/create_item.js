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

function update_categories_and_traits() {
  var selected_categories = $('#categories_selected').val();
  $.ajax({
    url: "/ctrlpyme4/item/trait_selector_data.json/" + item_id + "?categories=" + selected_categories
  })
  .done(function(data) {
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

console.log('script');


// #TODO:30 add parent category selection, when selecting a child.
$('#categories_tree').bind('nodeChecked nodeUnchecked', function(event, node) {
  var selected = $('#categories_tree').treeview('getChecked');
  var selected_categories = "";
  for(var i = 0; i < selected.length; i++) {
    selected_categories += selected[i].category_id;
    if (i < selected.length - 1) {
      selected_categories += ',';
    }
  }
  $('#categories_selected').prop('value', selected_categories);
  update_categories_and_traits();
  // $.ajax({
  //   url: "/ctrlpyme4/item/trait_selector_data.json?categories=" + selected_categories
  // })
  // .done(function(data) {
  //   if (data.status == "1") {
  //   }
  //   if (data.status == "no traits") {
  //     return;
  //   }
  //   $('#traits_tree').treeview({
  //     data: data.traits,
  //     multiSelect: true,
  //     selectedIcon: 'fa fa-check',
  //     expandIcon: 'fa fa-plus',
  //     collapseIcon: 'fa fa-minus',
  //     highlightSelected: false,
  //     levels: 1
  //   });
  //
  //   $('#traits_tree').bind('nodeSelected nodeUnselected', function(event, node) {
  //     var siblings = $('#traits_tree').treeview('getSiblings', node);
  //     var selected_traits = "";
  //     for(var i = 0; i < siblings.length; i++) {
  //       $('#traits_tree').treeview('unselectNode', [ siblings[i], { silent: true } ]);
  //     }
  //     var selected = $('#traits_tree').treeview('getSelected');
  //     var selected_traits = "";
  //     for(var i = 0; i < selected.length; i++) {
  //       selected_traits += selected[i].trait_id;
  //       if (i < selected.length - 1) {
  //         selected_traits += ',';
  //       }
  //     }
  //     $('#traits_selected').prop('value', selected_traits);
  //   });
  //
  // })
  // .fail(function(data) {
  //   console.log(data);
  // });
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


// check for repeated barcodes
$('#item_sku,#item_ean,#item_upc').change(function(event) {
  console.log('barcode_change');
});

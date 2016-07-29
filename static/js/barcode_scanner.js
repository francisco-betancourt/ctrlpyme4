function BarcodeScanner(id_suffix, container) {
  var clone = $(document.importNode($('#proto_scanner')[0].content, true));
  var scanner_form_id = 'barcode_scanner_form';
  var scanner_input_id = 'barcode';
  if (id_suffix) {
    scanner_form_id += '__' + id_suffix;
    scanner_input_id += '__' + id_suffix;
  }
  clone.find('.scanner-form').attr('id', scanner_form_id);
  clone.find('.scanner-input').attr('id', scanner_input_id);

  if (container) {
    container.append(clone);
    clone = $('#' + scanner_form_id);
  }
  var SCANNER_HTML = clone;


  // used when the query returns multiple items
  var matched_items = {};



  this.setup = function(success_callback, fail_callback, requirement, url) {
    var items = false;
    if (!url) {
      url = DEFAULT_BARCODE_SCANNER_URL;
      items = true;
    }

    $(SCANNER_HTML).on('submit', function(event) {
      event.preventDefault();

      var barcode = SCANNER_HTML.find('.scanner-input').val();

      if ((requirement && requirement(barcode)) || !requirement) {
        $.ajax({
          url: url + barcode
        })
        .done(function(data) {
          if (items) {
            // only one element found
            if (data.items.length == 1) {
              success_callback(data.items[0], barcode);
            }
            else {
              // if the first item matches the specified barcode then we dont show multiple results
              if (data.items[0].sku == barcode
                || data.items[0].ean == barcode
                || data.items[0].upc == barcode
              ) {
                success_callback(data.items[0], barcode);
              }
              else {
                SCANNER_HTML.find('.results').show();

                // create the matched items list
                for (var index in data.items) {
                  var item = data.items[index];
                  matched_items['r_item_' + item.id] = item;

                  var clone = $(document.importNode(
                    $('#proto_scanner__result_element')[0].content, true)
                  );
                  var clone_content = clone.find('.scanner-result-element');
                  clone_content.text(item.name);
                  clone_content[0].dataset.item_id = item.id;

                  SCANNER_HTML.find('.results').append(clone);

                  clone_content.on('click', function (event) {
                    var item_id = event.target.dataset.item_id;
                    item = matched_items['r_item_' + item_id];
                    success_callback(item, barcode);

                    // clean previous query results
                    SCANNER_HTML.find('.results').children().remove();
                    matched_items = {};
                    SCANNER_HTML.find('.results').hide();
                  });
                }
              }

            }
          }
          else
            success_callback(data, barcode);
          SCANNER_HTML.find('.scanner-input').val('');
          SCANNER_HTML.find('.scanner-input').blur();
        })
        .fail(function(data) {
          fail_callback(data, barcode);
        });
      }

      return false;
    });
  }

  return this;
}



function create_scanner(id_suffix, container) {
  // clone proto scanner
  var clone = $(document.importNode($('#proto_scanner')[0].content, true));
  var scanner_form_id = 'barcode_scanner_form';
  var scanner_input_id = 'barcode';
  if (id_suffix) {
    scanner_form_id += '__' + id_suffix;
    scanner_input_id += '__' + id_suffix;
  }
  clone.find('.scanner-form').attr('id', scanner_form_id);
  clone.find('.scanner-input').attr('id', scanner_input_id);

  if (container) {
    container.append(clone);
    clone = $('#' + scanner_form_id);
  }
  return clone;
}

function setup_scanner(scanner, success_callback, fail_callback, requirement, url) {

  var items = false;
  if (!url) {
    url = DEFAULT_BARCODE_SCANNER_URL;
    items = true;
  }

  $(scanner).on('submit', function(event) {
    event.preventDefault();

    var barcode = scanner.find('.scanner-input').val();

    if ((requirement && requirement(barcode)) || !requirement) {
      $.ajax({
        url: url + barcode
      })
      .done(function(data) {
        if (items) {
          // only one element found
          if (data.items.length == 1) {
            success_callback(data.items[0], barcode);
          }
          else {
            // create the matched items list
            for (var index in data.items) {
              var item = data.items[index];

              var clone = $(document.importNode(
                $('#proto_scanner__result_element')[0].content, true)
              );
              var clone_content = clone.find('.scanner-result-element');
              clone_content.text(item.name);
              clone_content[0].dataset.item_id = item.id;
              //clone.textContent = data.items[index].name;
              scanner.find('.results').append(clone);

              clone_content.on('click', function (event) {
                var item_id = event.target.dataset.item_id;
                item = items['r_item_' + item_id]
                success_callback(item, barcode);
              });
            }
            //success_callback(data.items[0], barcode);
          }
        }
        else
          success_callback(data, barcode);
        scanner.find('.scanner-input').val('');
      })
      .fail(function(data) {
        fail_callback(data, barcode);
      });
    }

    return false;
  });
};

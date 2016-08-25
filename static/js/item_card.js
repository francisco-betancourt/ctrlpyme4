
ITEM_CARDS = (function () {

  var M = {};

  var d = 0;


  function create_item_card(item) {
    var proto = document.getElementById('proto_item_card');
    var clone = document.importNode(proto.content, true);
    clone = $(clone);

    var card_image = clone.find('.card-image');
    card_image.css('background-image', 'url(' + item.image_path + ')');
    card_image.attr('href', card_image[0].href + '/' + item.id);

    clone.find('.item-card-name').text(item.name);
    clone.find('.availability').text(item.availability.text);

    if (item.availability.available) {
      clone.find('.availability').addClass('text-success');
    } else {
      clone.find('.availability').addClass('text-danger');
    }

    clone.find('.item-card-brand').text(item.brand.name);

    if (item.name_extra) {
      clone.find('.text-content').text(item.name_extra);
    } else {
      clone.find('.text-content').remove();
    }

    if (item.discount) {
      clone.find('.discount').text(item.discount + " %");
      clone.find('.old-price').text("$ " + item.base_price.toFixed(2));
    } else {
      clone.find('.discount-container').remove();
      clone.find('.old-price-container').remove();
    }
    clone.find('.price').text("$ " + item.price.toFixed(2));

    var dropdown_id = 'pop_menu_' + item.id;
    clone.find('.options-dropdown').attr('id', dropdown_id);
    clone.find('.options-dropdown-list').attr('aria-labelledby', dropdown_id);

    clone.find('.options-dropdown-list a').each(function (index, e) {
      e.href = e.href + '/' + item.id;
    });

    clone.find('.add-to-bag').attr('onclick', 'add_bag_item('+ item.id +')');

    var card = clone.find('.card')[0];
    $(card).css('animation-delay', d + 's');
    $(card).addClass('invisible');
    card.addEventListener('animationstart', function(event) {
      $(event.target).removeClass('invisible');
    }, false);

    d += .1;

    return clone;

  }


  function create_item_cards(items, container) {
    d = 0;

    for (var index in items) {
      var clone = create_item_card(items[index]);
      container.append(clone);
    }
  }


  function fetch_items(url, container) {
    $.ajax({
      url: url
    })
    .done(function (res) {

      create_item_cards(res.items, container);
    })
    .fail(function (res) {
      console.log(res);
    });
  }
  M.fetch_items = fetch_items;


  return M;
})();

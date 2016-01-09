# -*- coding: utf-8 -*-
#
# Author: Daniel J. Ramirez

import math


def pages_menu(query, page=0, ipp=10):
    """ Returns the rows matched by the query with a pagination menu, with the default page 'page' and 'ipp' items per page """

    try:
        page = int(page or 0)
        ipp = int(ipp or 10)
    except:
        page = 0
        ipp = 10

    start = page * ipp
    end = start + ipp
    total_rows_count = db(query).count()
    pages_count = total_rows_count / ipp
    page = int(min(page, pages_count))
    page = int(max(0, page))

    next_page_vars = dict(**request.vars)
    next_page_vars['page'] = page + 1
    next_page_vars['ipp'] = ipp
    next_url = URL(request.controller, request.function, args=request.args, vars=next_page_vars)

    prev_page_vars = dict(**request.vars)
    prev_page_vars['page'] = page - 1
    prev_page_vars['ipp'] = ipp
    prev_url = URL(request.controller, request.function, args=request.args, vars=prev_page_vars)

    prev_disabled, next_disabled = '', ''
    if page == 0:
        prev_disabled = 'disabled'
        prev_url = '#'
    if page == pages_count:
        next_disabled = 'disabled'
        next_url = '#'
    prev_link = LI(A(I(_class="fa fa-arrow-left"), _href=prev_url), _class="%s" % prev_disabled)
    next_link = LI(A(I(_class="fa fa-arrow-right"), _href=next_url), _class="%s" % next_disabled)

    pages_menu = DIV(UL(prev_link, LI(ipp), next_link, _class="pager") )

    return pages_menu, (start, end)


def stock_info(item):
    available = True
    stock = 0
    if auth.has_membership('Employee'):
        stock = item_stock(item, session.store)['quantity']
        stock = fix_item_quantity(item, stock)
        if stock <= 0:
            stock = SPAN(T('Out of stock'), _class="text-danger")
            available = False
        else:
            stock = str(stock) + " " + T('Available')
    else:
        stock = item_stock(item)['quantity']
        if stock <= 0:
            stock = SPAN(T('Out of stock'), _class="text-danger")
            available = False
        else:
            stock = SPAN(T('Available'), _class="text-success")

    return stock


def item_options(item):
    options_container = DIV(_class="btn-group btn-group-justified", _role="group")
    if auth.has_membership('Employee'):
        if auth.has_membership('Items info') or auth.has_membership('Items management') or auth.has_membership('Items prices'):
            options_container.append(
                DIV(
                    BUTTON(I(_class="fa fa-pencil"), _class="btn btn-default", _onclick="update_item(current_item_id)"
                    ),
                    BUTTON(I(_class="fa fa-picture-o"), _class="btn btn-default", _onclick="add_item_images(current_item_id)"
                    ),
                    _class="btn-group"
                )
            )



def item_card(item):
    """ """

    available = "Not available"
    available_class = "label label-danger"

    # stock, available = stock_info(item)

    stock_qty = 0
    if not session.store:
        stock_data = item_stock(item)
        stock_qty = stock_data['quantity']
    else:
        stock_data = item_stock(item, session.store)
        stock_qty = stock_data['quantity']
    if stock_qty > 0:
        available_class = "label label-success"
        available = "Available"

    item_options = DIV()

    bg_style = ""
    images = db(
        (db.item_image.id_item == db.item.id)
      & (db.item.name == item.name)
      & (db.item.is_active == True)
    ).select(db.item_image.ALL)
    if images:
        bg_style = "background-image: url(%s);" % URL('default','download', args=images.first().md)

    brand_link = H4(A(item.id_brand.name, _href=URL('item', 'get_by_brand', args=item.id_brand.id))) if item.id_brand else H4(T('No brand'))

    item_price = (item.base_price or 0) + item_taxes(item, item.base_price)

    return DIV(
        DIV(_class="panel-heading", _style=bg_style),
        DIV(
            H4(A(item.name, _href=URL('item', 'get_by_name', args=item.name))),
            brand_link,
            # P(item.description, _class="description"),
            DIV(
                SPAN(T(available), _class=available_class + ' item-available'),
                H4('$ ', DQ(item_price, True), _class="item-price"),
                _class="item-card-bottom"
            ),
            _class="panel-body"
        ),
        _class="panel panel-default item-card"
    )


# def

def item_images(id_item):
    """ Item upload form """

    images = db(db.item_image.id_item == id_item).select()

    img_container = DIV(_class="images-container")
    for image in images:
        img_container.append(IMG(_src=URL('default', 'download', args=image.image), _class="item-image"))
    form = SQLFORM(db.item_image)
    if form.process().accepted:
        print "success"
        # img_container.append()
    return img_container




def filter_menu(filter_data):
    """ """

    tablename = filter_data['tablename']
    sort_options = SELECT(_class="form-control")
    for sort_option in filter_data['sortby']:
        sort_options.append(OPTION(db[tablename][sort_option].label, _value=sort_option))

    return DIV(
        DIV(
            H5(T("Order by")),
            sort_options,
            _class="panel-body"
        ),
        _class="panel panel-default"
    )


def option_btn(icon_name, action_url=None, action_name='', onclick=None):
    click_action = onclick if onclick else 'window.location.href = "%s"' % action_url
    button = BUTTON(I(_class='fa fa-%s' % icon_name), T(action_name), _type='button', _class='btn btn-default', _onclick=click_action)
    return button

def row_options(row, update=False, delete=False, get=False):
    options = DIV()
    if get:
        options.append(option_btn(''))
    if update:
        options.append(option_btn('pencil', URL(request.controller, 'update', args=row.id)))
    if delete:
        options.append(option_btn('eye-slash', URL(request.controller, 'delete', args=row.id)))
    return options



def default_row_function(row, fields):
    """ Returns a row with the columns specified by fields, from the specified row """

    tr = TR()
    for field in fields:
        tr.append(TD(row[field]))

    return tr



def hide_button(row):
    """" Returns a button that calls the delete_row javascript function """

    return option_btn('eye-slash', onclick='delete_rows("/%s", "", "")' % (row.id))


def default_options_function(row):
    """ Returns a column with a generci edit option and genertic delete javascript option """

    td = TD()
    # edit option
    td.append(option_btn('pencil', URL('update', args=row.id)))
    td.append(option_btn('eye-slash', onclick='delete_rows("/%s", "", "")' % (row.id)))
    return td


def super_table(table, fields, query, row_function=default_row_function,
                options_function=default_options_function, options_enabled=True,
                show_id=False, selectable=False, custom_headers=[],
                extra_options=None, paginate=True, orderby=None):
    """ Returns a data table with the specified rows obtained from the specified query, if a row function is supplied then rows will follow the format established by that function, meaning that the row function should return a TR element, the row function has access to the row object and the fields array, if an options function is specified, then, option buttons will be appended as a row column (You must set options_enabled to True). The options_function must return a TD element. Set show_id True if you want the table to display the id for every row, Set selectable to True if you want a multiselect environment, the multiselect work via javascript, so you will have a list of selected row ids. If custom headers is not empty, those items will be used as the table headers, id and select will not be affected. extra_options is a function that will return a list of elements based on the specified row, that will be appended to the default options or the specified options (even though its not necesary to use extra options in a custom options environment).

        This function will use the database table field labels as table headers.
    """

    orderby_field = request.vars.orderby
    if not orderby_field:
        orderby_field = 'id'

    if not query:
        return None
    pages = ''
    if paginate:
        pages, limits = pages_menu(query, request.vars.page, request.vars.ipp)
    else:
        limits = (0, -1)

    orderby = db[table][orderby_field] if not orderby else orderby

    if request.vars.ascendent == 'True' or not request.vars.ascendent:
        request.vars.ascendent = 'True'
        rows = db(query).select(db[table].ALL, limitby=limits, orderby=orderby)
    else:
        request.vars.ascendent = 'False'
        rows = db(query).select(db[table].ALL, limitby=limits, orderby=~orderby)
    if not rows:
        return None

    thead = TR()
    if selectable:
        thead.append(TH(INPUT(_type='checkbox', _id='master_checkbox'), _class="table-selector"))
    if show_id:
        fields.insert(0, 'id')
    if custom_headers:
        for header in custom_headers:
            thead.append(TH(T(header)))
    else:
        for field in fields:
            header_class = ''
            label = db[table][field].label
            if field == 'id':
                label = '#'
                header_class = 'table_id'
            new_vars = dict(**request.vars)
            new_vars['orderby'] = field
            caret = ''
            # second consecutive click on field name, produces reverse order
            if request.vars.orderby == field:
                if request.vars.ascendent == 'True':
                    caret = 'up'
                    new_vars['ascendent'] = False
                else:
                    caret = 'down'
                    new_vars['ascendent'] = True
            order_url = URL(request.controller, request.function, args=request.args, vars=new_vars)
            thead.append(TH(A(label, _href=order_url), " ", I(_class="fa fa-caret-%s" % caret), _class=header_class))
    if options_enabled:
        thead.append(TH(T('Options'), _class='table-options'))
    thead = THEAD(thead)

    tbody = TBODY()
    for row in rows:
        tr = row_function(row, fields)
        if selectable:
            tr.insert(0, INPUT(_type='checkbox', _class='row_checkbox', _value=row.id))
        if options_enabled:
            options_td = options_function(row)
            if extra_options:
                for extra_option in extra_options(row):
                    options_td.append(extra_option)
            tr.append(options_td)

        tbody.append(tr)
    table = DIV(TABLE(thead, tbody, _class="table table-hover"), pages)

    return table


def create_ticket(title, store, seller, items, barcode, footer):
    store_data = P()
    if store:
        store_data.append(T('Store') + ': %s' % store.name)
        store_data.append(BR())
        store_data.append("%s %s %s %s %s %s %s %s" % (
            store.id_address.street
            , store.id_address.exterior
            , store.id_address.interior
            , store.id_address.neighborhood
            , store.id_address.city
            , store.id_address.municipality
            , store.id_address.state_province
            , store.id_address.country
        ))
    items_list = DIV(_id="items_list")
    subtotal = D(0)
    taxes = {}
    total = D(0)
    if items:
        for item in items:
            try:
                item_name = item.product_name
                item_price = item.sale_price
                for tax in item.id_item.taxes:
                    if not taxes.has_key(str(tax.name)):
                        taxes[str(tax.name)] = D(0)
                    taxes[str(tax.name)] += item_price * (tax.percentage / DQ(100))
                subtotal += item_price
                total += item_price + item.sale_taxes
            except:
                item_name = item.id_bag_item.product_name
                item_price = item.id_bag_item.sale_price
            items_list.append(DIV(
                SPAN(DQ(item.quantity, True), _class="qty"),
                SPAN(item_name, _class="name"),
                SPAN('$ %s' % DQ(item_price, True), _class="price"),
                _class="item"
            ))

    total_data = DIV(_id="total_data")
    total_data.append(DIV(T('Subtotal') + ': %s' % DQ(subtotal, True)))
    for key in taxes.iterkeys():
        total_data.append(DIV(key + ': %s' % DQ(taxes[key], True)))
    total_data.append(DIV(T('Total') + ': %s' % DQ(total, True)))

    ticket = DIV(
        DIV(_class="logo"),
        P(title),
        P(COMPANY_NAME),
        store_data,
        items_list,
        total_data,
        DIV(_id="barcode"),
        P(TICKET_FOOTER, _id="ticket_footer"),
        SCRIPT(_type="text/javascript", _src=URL('static','js/jquery-barcode.min.js')),
        SCRIPT('$("#barcode").barcode({code: "%s", crc: false}, "code39");' % barcode),
        _id="ticket", _class="ticket"
    )

    return ticket


def sqlform_field(id, label, content):
    return DIV(
                LABEL(T(label), _class="control-label col-sm-3"),
                DIV(content, _class="col-sm-9", _id=id + '_contents' ),
                _id=id, _class="form-group"
            )

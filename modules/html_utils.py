# -*- coding: utf-8 -*-
#
# Copyright (C) 2016 Bet@net
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
#
# Author: Daniel J. Ramirez


import math
from gluon import *
from gluon.html import *
from gluon.storage import Storage
from item_utils import item_stock, item_taxes, fix_item_price, fix_item_quantity
from common_utils import INFO, DQ


def CB(selected=False, _id=""):
    return INPUT(_id=_id, _type='checkbox', _class="cp-checkbox", _name=_id), LABEL(ICON('check_box_outline_blank', _class="checkbox", html_vars=dict(_value='false')), _for=_id)


def discounts_list(discounts):
    T = current.T
    ul = UL(_class="list-group")

    for discount in discounts:
        li = LI(_class="list-group-item")
        li.append(B('%s%% %s' % (discount.percentage, T('OFF'))))
        li.append(' %s ' % T('for'))
        if discount.id_item:
            a_text = '%s %s %s' % (T('item'), discount.id_item.name, discount.id_item.id)
            a_href = URL('item', 'get_item', args=discount.id_item.id)
        if discount.id_brand:
            a_text = '%s %s' % (T('brand'), discount.id_brand.name)
            a_href = URL('item', 'get_by_brand', args=discount.id_brand.id)
        if discount.id_category:
            a_text = '%s %s' % (T('category'), discount.id_category.name)
            a_href = URL('item', 'browse', vars=dict(category=discount.id_category.id))
        li.append(A(a_text, _href=a_href, _target='_blank'))
        if discount.code:
            li.append(' %s: ' % T('using code'))
            li.append(B(discount.code))
        ul.append(li)
    return ul


def ICON(icon_name, _id="", _class="", html_vars={}):
    # icon_name = icon_name.replace('-', '_')
    return I(icon_name, _class="material-icons %s" % (_class), _id=_id, **html_vars)


def INFO_CARD():
    session = current.session
    content = DIV(_class="panel-body")
    content.append(DIV(ICON('close', _class="close", _id="info_close")))
    hidden = False
    if not session.info:
        session.info = INFO(' ', ' ', '#', ' ')
        hidden = True
    if type(session.info) == str:
        content.append(DIV(session.info, _id="info_card__text"))
    if type(session.info) == dict:
        if session.info.has_key('text'):
            content.append(DIV(session.info['text'], _id="info_card__text"))
        if session.info.has_key('btn'):
            btn_data = session.info['btn']
            target = btn_data['target'] if btn_data.has_key('target') else ''
            href = btn_data['href'] if btn_data.has_key('href') else ''
            link_text = btn_data['text'] if btn_data.has_key('text') else ''
            if href:
                content.append(DIV(P(), A(link_text, _href=href, _target=target, _class="btn btn-default btn-block"), _id="info_card__btn_container"))
    if hidden:
        session.info = None
    return content


def MENU_ELEMENTS(submenu_prefix = '', menu=current.response.menu):
    # elements = []
    i = 0
    for menu_item in menu:
        res = Storage()
        menu_item_name = menu_item[0]
        url = ''
        submenu = []
        try:
            url = menu_item[2]
            submenu = menu_item[3]
        except:
            None
        if url:
            res.menu = A(menu_item_name, _href=url, _class="menu-element")
            yield res
        else:
            menu = DIV(
                _class="menu-element", _onclick="toggle_submenu('%s_%s')" % (submenu_prefix, i)
            )
            if submenu:
                sub = DIV(_class="submenu primary-color-dim", _id="submenu_%s_%s" % (submenu_prefix, i), _hidden="hidden"
                    )
                i += 1
                for submenu_item in submenu:
                    submenu_item_name = submenu_item[0]
                    suburl = '#'
                    try:
                        suburl = submenu_item[2]
                    except:
                        None
                    sub.append(A(submenu_item_name, _href=suburl, _class="menu-element"))
                # menu.append(sub)
                res.submenu = sub
            menu.append(DIV(menu_item_name, ICON('arrow_drop_down', _class="add-on"), _class="menu-text"))
            res.menu = menu
            yield res




def pages_menu_bare(query, page=0, ipp=10, distinct=None):
    """ Returns the rows matched by the query with a pagination menu, with the default page 'page' and 'ipp' items per page """

    request = current.request
    db = current.db

    start = page * ipp
    end = start + ipp
    total_rows_count = db(query).count(distinct=distinct)
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
    if page == 0:
        prev_url = '#'
    if page == pages_count:
        next_url = '#'

    return prev_url, next_url, (start, end), pages_count


def pages_menu(query, page=0, ipp=10, distinct=None):
    try:
        page = int(page or 0)
        ipp = int(ipp or 10)
    except:
        page = 0
        ipp = 10
    prev_url, next_url, limits, pages_count = pages_menu_bare(query, page, ipp, distinct)

    prev_disabled, next_disabled = '', ''
    prev_link = LI(A(ICON('arrow_back'), _href=prev_url))
    next_link = LI(A(ICON("arrow_forward"), _href=next_url))
    pages_menu = DIV(UL(prev_link, LI(ipp), next_link, _class="pager") )

    return pages_menu, limits


def stock_info(item):
    auth = current.auth
    T = current.T
    session = current.session

    available = True
    stock = 0

    if auth.has_membership('Employee') and item.has_inventory:
        stock = item_stock(item, session.store)['quantity']
        stock = fix_item_quantity(item, stock)
        if stock <= 0:
            stock = SPAN(T('Out of stock'), _class="text-danger")
            available = False
        else:
            stock = str(stock) + " %s %s " % (item.id_measure_unit.symbol, T('Available'))
    else:
        stock = item_stock(item)['quantity']
        if stock <= 0:
            stock = SPAN(T('Out of stock'), _class="text-danger")
            available = False
        else:
            stock = SPAN(T('Available'), _class="text-success")

    return stock


def create_item_options(item):
    options_container = DIV(_class="btn-group btn-group-justified", _role="group")
    if auth.has_membership('Employee'):
        if auth.has_membership('Items info') or auth.has_membership('Items management') or auth.has_membership('Items prices'):
            options_container.append(
                DIV(
                    BUTTON(ICON("edit"), _class="btn btn-default", _onclick="update_item(current_item_id)"),
                    _class="btn-group", _role="group"
                )
            )
            options_container.append(
                DIV(
                    BUTTON(ICON("edit"), _class="btn btn-default", _onclick="update_item(current_item_id)"
                    ),
                    _class="btn-group", _role="group"
                )
            )
        return options_container
    return None



def item_card(item):
    """ """
    session = current.session
    auth = current.auth
    db = current.db
    T = current.T

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
      & (db.item.id == item.id)
      & (db.item.is_active == True)
    ).select(db.item_image.ALL)
    if images:
        bg_style = "background-image: url(%s);" % URL('static','uploads/'+ images.first().md)
    else:
        bg_style = "background-image: url(%s);" % URL('static', 'images/no_image.svg')

    brand_link = H4(A(item.id_brand.name, _href=URL('item', 'get_by_brand', args=item.id_brand.id))) if item.id_brand else H4(T('No brand'))

    item_price = (item.base_price or 0) + item_taxes(item, item.base_price)
    fix_item_price(item, item.base_price)
    item_price = item.discounted_price

    item_price_html = DIV()
    if item.discount_percentage > 0:
        item_price_html.append(DIV(T('before'), SPAN('$ ', SPAN(item.new_price, _class="old-price"), _class="right")))
        item_price_html.append(
            DIV(T('discount'), SPAN(SPAN(item.discount_percentage), '%', _class="right text-danger"))
        )
    item_price_html.append(
        DIV(
            SPAN(T(available), _class=available_class + ' item-available'),
            H4('$ ', DQ(item_price, True), _class="item-price"),
            _class="item-card-bottom"
        )
    )

    # item options
    item_options = DIV(
        BUTTON(ICON('shopping_basket'), _type="button", _class="btn btn-default", _onclick="add_bag_item(%s)" % item.id)
        , _class="btn-group item-options"
    )
    if auth.has_membership('Employee'):
        expand_btn = BUTTON(ICON('more_vert'), _type="button", _class="btn btn-default dropdown-toggle", data={'toggle':'dropdown'})
        item_options.append(expand_btn)
        options_ul = UL(_class="dropdown-menu")
        if auth.has_membership('Items info') or auth.has_membership('Items management') or auth.has_membership('Items prices'):
            options_ul.append(LI(A(T('Update'), _href=URL('item', 'update', args=item.id))))
            options_ul.append(LI(A(T('Print labels'), _href=URL('item', 'labels', args=item.id))))
            options_ul.append(LI(A(T('Add images'), _href=URL('item_image', 'create', args=item.id))))
        if auth.has_membership('Analytics'):
            options_ul.append(LI(A(T('Analysis'), _href=URL('analytics', 'item_analysis', args=item.id))))
        item_options.append(options_ul)


    # concatenate all the item traits, this string will be appended to the item name
    traits_str = ''
    traits_ids = ''
    item_url = URL('item', 'get_item', args=item.id)
    item_name = item.name
    if item.traits:
        for trait in item.traits:
            traits_ids += str(trait.id)
            traits_str += trait.trait_option + ' '
            if trait != item.traits[-1]:
                traits_ids += ','
        item_url = URL('item', 'get_item', vars=dict(name=item.name, traits=traits_ids))
        item_name = item.name + ' ' + traits_str
    elif item.description:
        item_name += ' - ' + item.description[:10]
        if len(item.description) > 10:
            item_name += '...'

    return DIV(
        A('', _class="panel-heading", _style=bg_style, _href=item_url),
        DIV(
            DIV(H4(A(item_name, _href=item_url)), brand_link,
                _class="item_data"
            ),
            item_options,
            # create_item_options(item),
            # P(item.description, _class="description"),
            item_price_html,
            _class="panel-body"
        ),
        _class="panel panel-default item-card shadow-1"
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

    T = current.T
    db = current.db
    request = current.request

    tablename = filter_data['tablename']
    sort_options = SELECT(_class="form-control")
    for sort_option in filter_data['sortby']:
        sort_options.append(
            OPTION(db[tablename][sort_option].label, _value=sort_option, _onclick="window.location.href = '%s';" % URL('default', request.function, args=request.args, vars=dict(sorting=sort_option))
            )
        )

    return DIV(
        DIV(
            H5(T("Order by")),
            sort_options,
            _class="panel-body"
        ),
        _class="panel panel-default"
    )


def option_btn(icon_name, action_url=None, action_name='', onclick=None):
    T = current.T

    click_action = onclick if onclick else 'window.location.href = "%s"' % action_url
    button = BUTTON(ICON(icon_name), T(action_name), _type='button', _class='btn', _onclick=click_action)
    return button

def row_options(row, update=False, delete=False, get=False):
    options = DIV()
    if get:
        options.append(option_btn(''))
    if update:
        options.append(option_btn('edit', URL(request.controller, 'update', args=row.id)))
    if delete:
        options.append(option_btn('visibility_off', URL(request.controller, 'delete', args=row.id)))
    return options



def default_row_function(row, fields):
    """ Returns a row with the columns specified by fields, from the specified row """

    tr = TR()
    for field in fields:
        tr.append(TD(row[field]))

    return tr


def hide_button(row):
    """" Returns a button that calls the delete_row javascript function """

    return option_btn('visibility_off', onclick='delete_rows("/%s", "", "")' % (row.id))


def default_options_function(row):
    """ Returns a column with a generic edit option and delete javascript option """

    td = TD()
    # edit option
    td.append(option_btn('edit', URL('update', args=row.id)))
    td.append(option_btn('visibility_off', onclick='delete_rows("/%s", "", "")' % (row.id)))
    return td


def super_table(table, fields, query, row_function=default_row_function,
                options_function=default_options_function, options_enabled=True,
                show_id=False, selectable=False, custom_headers=[],
                extra_options=None, paginate=True, orderby=None, search_enabled=True):
    """ Returns a data table with the specified rows obtained from the specified query, if a row function is supplied then rows will follow the format established by that function, meaning that the row function should return a TR element, the row function has access to the row object and the fields array, if an options function is specified, then, option buttons will be appended as a row column (You must set options_enabled to True). The options_function must return a TD element. Set show_id True if you want the table to display the id for every row, Set selectable to True if you want a multiselect environment, the multiselect work via javascript, so you will have a list of selected row ids. If custom headers is not empty, those items will be used as the table headers, id and select will not be affected. extra_options is a function that will return a list of elements based on the specified row, that will be appended to the default options or the specified options (even though its not necesary to use extra options in a custom options environment).

        This function will use the database table field labels as table headers.
    """

    request = current.request
    db = current.db
    T = current.T

    orderby_field = request.vars.orderby
    if not orderby_field:
        orderby_field = 'id'

    term = request.vars.term
    if term and search_enabled:
        s_query = (db[table].id < 0)
        for t_field in fields:
            if db[table][t_field].type == 'string':
                s_query |= (db[table][t_field].contains(term))
            if db[table][t_field].type == 'integer' or db[table][t_field].type.split(' ')[0] == 'reference':
                try:
                    int(term)
                    s_query |= (db[table][t_field] == term)
                except:
                    pass

        query &= s_query

    if not query:
        return None
    pages = ''
    if paginate:
        pages, limits = pages_menu(query, request.vars.page, request.vars.ipp)
    else:
        # TODO fix this
        limits = (0, 100)

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
            thead.append(TH(A(label, _href=order_url), " ", ICON("arrow_drop_%s" % caret), _class=header_class))
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

    filter_form = FORM(INPUT(_id='table_filter_term', _class="form-control"), INPUT(_type="submit", _value=T('Search')), _id="table_filter", _class="form-inline")
    form_script = SCRIPT("$('#table_filter').submit(function (event) {window.location.href = '%s?term=' + $('#table_filter_term').val(); event.preventDefault()})" % URL(request.controller, request.function))
    if not search_enabled:
        filter_form = ''
        form_script = ''

    table = DIV(filter_form, TABLE(thead, tbody, _class="table table-hover"), pages, form_script)

    return table


def sqlform_field(id, label, content):
    return DIV(
                LABEL(T(label), _class="control-label col-sm-3"),
                DIV(content, _class="col-sm-9", _id=id + '_contents' ),
                _id=id, _class="form-group"
            )

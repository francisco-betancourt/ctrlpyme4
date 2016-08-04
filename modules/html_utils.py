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
from item_utils import item_stock_qty, item_taxes, fix_item_price, fix_item_quantity, item_barcode
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
            brand = discount.id_brand.name
            a_text = '%s %s' % (T('brand'), brand.name)
            a_href = URL('item', 'browse', vars=dict(brand=brand.id))
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




def pages_menu_bare(query, page=0, ipp=10, distinct=None, index=None):
    """ Returns the rows matched by the query with a pagination menu, with the default page 'page' and 'ipp' items per page, index is used as a postfix in the generated vars, this function does not return HTML, it return data useful for generating the required HTML """

    request = current.request
    db = current.db

    ipp = min(ipp, 100)
    start = page * ipp
    end = start + ipp
    total_rows_count = db(query).count(distinct=distinct)
    mod = 1 if not total_rows_count % ipp else 0
    pages_count = total_rows_count / ipp - mod
    page = int(min(page, pages_count))
    page = int(max(0, page))

    page_key = 'page'
    ipp_key = 'ipp'
    if index != None and type(index) == int:
        page_key += '_%s' % index
        ipp_key += '_%s' % index

    next_page_vars = dict(**request.vars)
    next_page_vars[page_key] = page + 1
    next_page_vars[ipp_key] = ipp
    next_url = URL(request.controller, request.function, args=request.args, vars=next_page_vars)

    prev_page_vars = dict(**request.vars)
    prev_page_vars[page_key] = page - 1
    prev_page_vars[ipp_key] = ipp
    prev_url = URL(request.controller, request.function, args=request.args, vars=prev_page_vars)
    if page == 0:
        prev_url = '#'
    if page == pages_count:
        next_url = '#'

    return prev_url, next_url, (start, end), pages_count


def pages_menu(query, page=0, ipp=10, distinct=None):
    """ Returns a generic pagination menu, paginating over the results of the query """

    try:
        page = int(page or 0)
        ipp = min(int(ipp or 10), 100)
    except:
        page = 0
        ipp = 10
    prev_url, next_url, limits, pages_count = pages_menu_bare(query, page, ipp, distinct)

    prev_disabled, next_disabled = '', ''
    prev_link = A(ICON('arrow_back'), _href=prev_url) if prev_url != '#' else ''
    next_link = A(ICON("arrow_forward"), _href=next_url) if next_url != '#' else ''
    pages_menu = DIV(DIV(prev_link, SPAN(ipp), next_link, _class="cp-pager") )

    return pages_menu, limits


def stock_info(item):
    auth = current.auth
    T = current.T
    session = current.session

    available = True
    stock = 0

    if auth.has_membership('Employee') and item.has_inventory:
        stock = item_stock_qty(item, session.store)
        stock = fix_item_quantity(item, stock)
        if stock <= 0:
            stock = SPAN(T('Out of stock'), _class="text-danger")
            available = False
        else:
            stock = str(stock) + " %s %s " % (item.id_measure_unit.symbol, T('Available'))
    else:
        stock = item_stock_qty(item)
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

    stock_qty = item_stock_qty(item, session.store)
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
        bg_style = "background-image: url(%s);" % URL('static','uploads/'+ images.first().sm)
    else:
        bg_style = "background-image: url(%s);" % URL('static', 'images/no_image.svg')

    brand_link = H4(
        A(item.id_brand.name,
          _href=URL('item', 'browse', vars=dict(brand=item.id_brand.id))
        )
    ) if item.id_brand else H4(T('No brand'))

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

    main_content = DIV(
        H4(A(item_name, _href=item_url)),
        brand_link,
        _class="item_data"
    )

    # item options
    item_options = DIV(
        BUTTON(ICON('shopping_basket'), _type="button", _class="btn btn-default", _onclick="add_bag_item(%s)" % item.id)
        , _class="btn-group item-options"
    )
    if auth.has_membership('Employee'):
        main_content.append(
            P('# ', SPAN(item_barcode(item)), _class="item-barcode")
        )

        expand_btn = BUTTON(ICON('more_vert'), _type="button", _class="btn btn-default dropdown-toggle", data={'toggle':'dropdown'})
        item_options.append(expand_btn)
        options_ul = UL(_class="dropdown-menu")
        if auth.has_membership('Items info') or auth.has_membership('Items management') or auth.has_membership('Items prices'):
            options_ul.append(
                LI(A(T('Update'), _href=URL('item', 'update', args=item.id)))
            )
            options_ul.append(
                LI(A(T('Print labels'), _href=URL('item', 'labels', args=item.id)))
            )
            options_ul.append(
                LI(A(T('Add images'), _href=URL('item_image', 'create', args=item.id)))
            )
        if auth.has_membership('Analytics'):
            options_ul.append(
                LI(A(T('Analysis'), _href=URL('analytics', 'item_analysis', args=item.id)))
            )
        item_options.append(options_ul)

    return DIV(
        A('', _class="panel-heading", _style=bg_style, _href=item_url),
        DIV(
            main_content,
            item_options,
            item_price_html,
            _class="panel-body"
        ),
        _class="panel panel-default item-card"
    )


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


def sqlform_field(id, label, content):
    return DIV(
                LABEL(T(label), _class="control-label col-sm-3"),
                DIV(content, _class="col-sm-9", _id=id + '_contents' ),
                _id=id, _class="form-group"
            )

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
# Author Daniel J. Ramirez <djrmuv@gmail.com>

import json
from gluon.storage import Storage
from item_utils  import *


def categories_tree_html(categories, item=None):
    # json object from python dict
    categories_tree = json_categories_tree(item)
    categories_selected_text = item.categories_selected_text if item else ''
    category_search = INPUT(_type="search", _id="category_search", _placeholder=T("search categories"), _class="form-control")
    categories_selected = INPUT(_value=categories_selected_text, _type="text", _id="categories_selected", _hidden=True, _name="categories_selected")
    # hack: this script sets the javascript variable categories_tree_data, to
    # the categories_tree json data, so it can be used inside the view.
    categories_tree_script = SCRIPT("categories_tree_data = %s;" % categories_tree)
    field = DIV(category_search, DIV(_id="categories_tree"), categories_selected, categories_tree_script, _class="col-sm-9")

    return DIV(LABEL(T('Categories'), _class="control-label col-sm-3"), field, _class="form-group")


def traits_widget(item=None):
    # get the item traits
    traits = item.traits if item and item.traits else []

    def create_tait_data_container():
        return DIV(
            DIV(
                INPUT(
                    _placeholder=T("Trait category name"),
                    _class='trait-category-name form-control',
                    _id='new_trait_category_name',
                    _list="new_trait_category_name_suggestions"
                ),
                TAG['datalist'](_id="new_trait_category_name_suggestions"),
                _class='trait-input-container'
            ),
            DIV(
                INPUT(
                    _placeholder=T("Trait option"),
                    _class='trait-option form-control',
                    _id='new_trait_option',
                    _list="new_trait_option_suggestions",
                ),
                TAG['datalist'](_id="new_trait_option_suggestions"),
                _class='trait-input-container'
            ),
            BUTTON(ICON('add'), _class='form-control', _id='new_trait_button'),
            _class="trait-values"
        )

    container = DIV(_class="traits-container col-sm-9")

    prototype_list_element = TAG['template'](
        LI(
            SPAN( B(_class='trait-name'), SPAN(_class='trait-option') ),
            ICON('close', _class='right remove-btn'),
            _class='list-group-item'
        ), _id='proto_trait_li'
    )
    current_traits = UL(_class='added-traits list-group', _id='current_traits')

    if item:
        traits_query = None
        for trait_id in traits:
            if not traits_query:
                traits_query = (db.trait.id == trait_id)
            else:
                traits_query |= db.trait.id == trait_id
        if traits_query:
            traits = db(traits_query).iterselect(
                db.trait.id_trait_category, db.trait.trait_option
            )
        else:
            traits = []
    traits_selected = ''
    for trait in traits:
        traits_selected += trait.id_trait_category.name + ':' + trait.trait_option + ','
    traits_selected = traits_selected[:-1]
    container.append(prototype_list_element)
    container.append(current_traits)
    container.append(create_tait_data_container())

    container = DIV(
        LABEL(T('Traits'), _class="control-label col-sm-3"),
        container,
        INPUT(_value=traits_selected, _type="text", _hidden=True, _id="traits_selected", _name="traits_selected"
        ),
        _class="form-group"
    )

    return container


def bundle_items_html():
    return DIV(
               LABEL(T('Bundle items'), _class="control-label col-sm-3")
               , DIV(DIV(_id='bundle_items_list', _class="list-group"),_class="col-sm-9")
               , _class="form-group", _id="bundle_items_form_group"
               , _hidden=True
           )


def item_form(item=None, is_bundle=False):
    is_bundle = bool(request.vars.is_bundle)

    fields = ['name', 'id_brand', 'description', 'id_measure_unit', 'allow_fractions']
    if auth.has_membership('Items management'):
        fields = ['name', 'sku', 'ean', 'upc', 'id_brand', 'description', 'has_inventory', 'id_measure_unit', 'taxes', 'allow_fractions', 'is_returnable', 'reward_points']
    if auth.has_membership('Items prices'):
        fields = ['name', 'sku', 'ean', 'upc', 'id_brand', 'description', 'has_inventory', 'base_price', 'price2', 'price3', 'id_measure_unit', 'taxes', 'allow_fractions', 'is_returnable', 'reward_points']

    # extra fields
    name_change_script = ''
    if EXTRA_FIELD_1_NAME:
        fields.insert(3, 'extra_data1')
        name_change_script += '$("#item_extra_data1__label").html("%s");' % EXTRA_FIELD_1_NAME
    if EXTRA_FIELD_2_NAME:
        fields.insert(3, 'extra_data2')
        name_change_script += '$("#item_extra_data2__label").html("%s");' % EXTRA_FIELD_2_NAME
    if EXTRA_FIELD_3_NAME:
        fields.insert(3, 'extra_data3')
        name_change_script += '$("#item_extra_data3__label").html("%s");' % EXTRA_FIELD_3_NAME

    form = SQLFORM(db.item, item, showid=False, fields=fields)
    form.append(SCRIPT(name_change_script));

    # categories
    categories = db(
        db.category.is_active==True
    ).iterselect(orderby=~db.category.parent)
    if categories:
        form[0].insert(4, categories_tree_html(categories, item))
        form[0].insert(5, traits_widget(item))

    if form.process().accepted:
        # categories
        l_categories = []  # categories selected
        for c in (form.vars.categories_selected or '').split(','):
            if not c:
                continue
            l_categories.append(int(c))
        # traits
        traits = []
        if item:
            traits = item.traits
        if request.vars.traits_selected:
            traits = create_traits_ref_list(request.vars.traits_selected)

        db.item(form.vars.id).update_record(
            url_name=item_url(form.vars.name, form.vars.id),
            is_bundle=is_bundle, traits=traits, categories=l_categories
        )
        session.flash = T('Item created') if not item else T('Item updated')
        # if the item is bundle, redirect to the bundle filling page
        if is_bundle and auth.has_membership('Items management'):
            redirect(URL('fill_bundle', args=form.vars.id))
        else:
            redirection(URL('index'))
    elif form.errors:
        response.flash = T('form has errors')
    return dict(form=form)


@auth.requires_membership('Items management')
def create():
    """
        vars:
            is_bundle: whether the newly created item will be a bundle or not
    """

    # return item_form(is_bundle=request.vars.is_bundle)
    redirect(URL('create_or_update', vars=request.vars))


@auth.requires(
       auth.has_membership('Items info')
    or auth.has_membership('Items management')
    or auth.has_membership('Items prices')
)
def create_or_update():
    """
        args:
            item: if this argument is present, then this function will return an update form
        vars:
            is_bundle: whether the newly created item will be a bundle or not
    """

    item = db.item(request.args(0))
    if not item and not auth.has_membership('Items management'):
        response.flash = T("You can't create items")
        redirect('index');

    is_bundle = request.vars.is_bundle
    if item and item.is_bundle:
        is_bundle = True
        request.vars.is_bundle = True
    forms = item_form(item=item, is_bundle=is_bundle)

    return dict(item=item, is_bundle=is_bundle, form=forms['form'])


@auth.requires_membership('Items management')
def fill_bundle():
    """
        args:
            item_id: the bundle item that will be filled.
    """

    bundle = db.item(request.args(0))
    if not bundle:
        raise HTTP(404)
    bundle_form = SQLFORM.factory(
        _id='bundle_form', buttons=[]
    )
    bundle_form[0].insert(0, bundle_items_html())
    bundle_items = db(db.bundle_item.id_bundle == bundle.id).select()
    if bundle_items:
        redirection()
    bundle_items_data = {}
    for b_item in bundle_items:
        barcode = b_item.id_item.sku or b_item.id_item.ean or b_item.id_item.upc
        if barcode:
            bundle_items_data['item_' + barcode] = {'id': b_item.id_item, 'qty': int(b_item.quantity), 'name': b_item.id_item.name, 'barcode': barcode}
    bundle_items_data = json.dumps(bundle_items_data)
    bundle_items_script = SCRIPT('bundle_items = %s;' % bundle_items_data)
    bundle_form.append(bundle_items_script)

    form = SQLFORM.factory(_id="master_form")
    form.append(INPUT(_id="final_bundle_items_list", _type="text", _hidden=True, _name='item_ids'))
    if form.process().accepted:
        for pair in form.vars.item_ids.split(','):
            if not pair:
                continue
            try:
                item_id, item_qty = pair.split(':')
                item = db(db.item.id == item_id).select().first()
                # we dont want bundles to be in bundles
                if not item or item.is_bundle:
                    continue

                item_qty = fix_item_quantity(item, item_qty)
                if not item_qty > 0:
                    continue
                # update_or_insert used because even if the interface does not support multiple items with the same id the user can modify the string to do such case.
                db.bundle_item.update_or_insert(
                      (db.bundle_item.id_bundle == bundle.id)
                    & (db.bundle_item.id_item == item_id),
                    quantity=item_qty,
                    id_bundle=bundle.id,
                    id_item=item.id
                )
            except ValueError:
                pass
        redirect(URL('index'))
        response.flash = T('form accepted')
    elif form.errors:
        response.flash = T('form has errors')
    else:
        response.flash = T('please fill the form')

    return locals()



def get():
    """
        args:
            item_id: the item that will be retrieved
    """
    item = db((db.item.id == request.args(0)) & (db.item.is_active == True) ).select().first()
    if not item:
        raise HTTP(404)
    return locals()


def get_item():
    """
        get the item specified by its id or name and traits
        args [item_id]
        vars {name, traits}
    """

    same_traits = False
    multiple_items = False

    try:
        long(request.args(0) or 0)
    except:
        raise HTTP(404)

    query = (db.item.id == request.args(0))

    return_data = dict()

    if not auth.is_logged_in() or (auth.user and auth.user.is_client):
        query &= db.item.is_active == True
    item = db(query).select().first()

    if not item or request.vars.name:
        item_name = request.vars.name

        # when traits are specified, only one item with the specified name and traits should match
        # this is the first item
        if request.vars.traits:
            traits = request.vars.traits.split(',')
            if not item:
                item = db(
                    (db.item.name == item_name)
                  & (db.item.traits.contains(traits, all=True))
                  & (db.item.is_active == True)
                ).select().first()
        elif not item:
            item = db(
                (db.item.name == item_name)
              & (db.item.is_active == True)
            ).select().first()
        if not item:
            raise HTTP(404)

        # base_trait_categories = [str(t.id_trait_category.id) for t in item.traits]
        # base_trait_categories.sort()
        # base_trait_categories = ','.join(base_trait_categories)
        item.traits_str = ','.join([str(t.id) for t in item.traits])

        # since there could be multiple items with the same name, we query all the items with the specified name different than the first item
        other_items = db(
            (db.item.name == item_name)
          & (db.item.id != item.id)
          & (db.item.is_active == True)
        ).select()
        if len(other_items) > 0:
            multiple_items = True

        #same_traits = True
        trait_options = {}

        if multiple_items:
            # check if all the items have the same traits
            for other_item in other_items:
                # other_trait_categories = [str(t.id_trait_category.id) for t in item.traits]
                # other_trait_categories.sort()
                # other_trait_categories = ','.join(other_trait_categories)
                other_item.traits_str = ','.join([str(t.id) for t in other_item.traits])

                # if base_trait_categories != other_trait_categories:
                #     same_traits = False
                #     break
        return_data['other_items'] = other_items

    if not item:
        raise HTTP(404)

    new_price = item.base_price or 0
    discounts = item_discounts(item)
    for discount in discounts:
        new_price -= new_price * DQ(discount.percentage / 100.0)
    new_price += item_taxes(item, new_price)

    item.barcode = item_barcode(item)
    item.base_price += item_taxes(item, item.base_price)
    discount_percentage = 0
    try:
        discount_percentage = int((1 - (new_price / item.base_price)) * 100)
    except:
        pass
    item.base_price = str(DQ(item.base_price, True))
    item.discounted_price = str(DQ(new_price, True))
    item.discount_percentage = discount_percentage
    stock = stock_info(item)
    images = db(db.item_image.id_item == item.id).select()

    page_title = item.name
    page_description = item.description + ' ' + ', '.join([cat.name for cat in  item.categories])

    return_data['item'] = item
    return_data['images'] = images
    return_data['page_title'] = page_title
    return_data['page_description'] = page_description
    return_data['stock'] = stock
    return_data['discounts'] = discounts
    return_data['same_traits'] = same_traits
    return_data['multiple_items'] = multiple_items

    return return_data


def find_by_code():
    """ Returns the items whose one of its barcodes matches the specified one

        args:
            item_code: the item EAN, UPC or SKU
    """
    item = db((db.item.ean == request.args(0))
            | (db.item.upc == request.args(0))
            | (db.item.sku == request.args(0))
           ).select().first()
    if not item:
        raise HTTP(404)
    return locals()


def find_by_matching_code():
    """ Returns items with a matching initial barcode

    for example:
        item1  #7771-a
        item2  #7771-b

    using barcode #7771 will return both, this is useful to have pseudo repeated
    barcodes.

    This function will return only the first ten results, and a data to query
    the next elements.
    """

    from item_utils import composed_name

    barcode = request.args(0)
    try:
        page = int(request.args(1)) or 0
    except:
        page = 0

    if not barcode:
        raise HTTP(405)

    start = page * 10
    end = start + 10

    items = db(
          (db.item.sku.startswith(barcode))
        | (db.item.upc.startswith(barcode))
        | (db.item.ean.startswith(barcode))
    ).select(
        db.item.ALL, limitby=(start, end),
        orderby=db.item.sku.length & db.item.upc.length & db.item.ean.length
    )

    # process the items
    for item in items:
        img = db(db.item_image.id_item == item.id).select().first()
        item.name = composed_name(item)

        if img:
            thumb = URL('static', 'uploads/' + img.thumb)
            item.thumb = thumb
        else:
            item.thumb = URL('static', 'images/no_image.svg')

    if not items:
        raise HTTP(404)

    return dict(items=items)


@auth.requires(auth.has_membership('Items management')
    or auth.has_membership('Items info')
    or auth.has_membership('Items prices')
)
def update():
    """
        vars:
            is_bundle: whether the newly created item will be a bundle or not
    """

    redirect(URL('create_or_update', args=request.args, vars=request.vars))


@auth.requires_membership('Items management')
def delete():
    return common_delete('item', request.args)


@auth.requires_membership('Items management')
def undelete():
    return common_undelete('item', request.args)


def item_options(row):
    buttons = ()
    if auth.has_membership('Items info') or auth.has_membership('Items prices') or auth.has_membership('Items management'):
        _vars = {'is_bundle': True} if row.is_bundle else {}
        buttons += OPTION_BTN('edit', URL('update', args=row.id, vars=_vars), title=T('edit')),
    # hide button
    if auth.has_membership('Items management'):
        buttons += supert_default_options(row)[1],
    buttons += OPTION_BTN('shopping_basket', _onclick="add_bag_item(%s);" % row.id, title=T('add to bag')),

    return buttons


@auth.requires(auth.has_membership('Employee') or auth.has_membership('Admin'))
def index():
    fields = [
        {
            'fields': ['name', 'is_bundle'],
            'custom_format': lambda row, fields: '%s %s' % (T('BUNDLE') if row.is_bundle else '', row.name),
            'label_as': T('Name')
        }, 'sku', 'ean', 'upc'
    ]
    if EXTRA_FIELD_1_NAME:
        fields.append({'fields': ['extra_data1'], 'label_as': EXTRA_FIELD_1_NAME})
    if EXTRA_FIELD_2_NAME:
        fields.append({'fields': ['extra_data2'], 'label_as': EXTRA_FIELD_2_NAME})
    if EXTRA_FIELD_3_NAME:
        fields.append({'fields': ['extra_data3'], 'label_as': EXTRA_FIELD_3_NAME})
    query = (db.item.is_active == True)
    if request.vars.show_hidden == 'yes':
        query = (db.item.id > 0)

    data = SUPERT(query, fields=fields, options_func=item_options, global_options=[visibility_g_option()])

    return locals()


def items_list(query, page, ipp=10):
    """ get the items with the specified query"""
    db(query).select(limitby)


def browse():
    """ Item browser
        vars: {category, sort, categories, is_service, brand, term}
    """

    term = request.vars.term;

    category = db.category(request.vars.category)
    is_service = request.vars.is_service == 'yes'
    brand = db.brand(request.vars.brand)

    title = T('Items')

    query = (db.item.is_active == True)

    if term:
        query = search_item_query(term, category)

    if category:
        query &= db.item.categories.contains(category.id)

    if is_service:
        title = T('Services')
        query &= db.item.has_inventory == False
    if brand:
        query &= db.item.id_brand == brand.id


    no_items_msg = T('No items found') + ' '
    if is_service:
        no_items_msg = T('No services found') + ' '
    if brand:
        no_items_msg += T('with brand: %s ') % brand.name
    if category:
        no_items_msg += T('in category: %s') % category.name


    pages, limits = pages_menu(query, request.vars.page, request.vars.ipp, distinct=db.item.name)
    items = db(query).select(limitby=limits)

    selected_categories = [category.id] if category else []
    categories_data_script = SCRIPT("var categories_tree_data = %s" % json_categories_tree(selected_categories=selected_categories))

    filter_data = {
        "tablename": "item",
        "sortby": ['base_price', 'name']
    }
    filter_data = None

    page_title = T('Browse items')
    page_description = T('Browse items catalog')

    return locals()


@auth.requires_membership('Items info')
def labels():
    """
        args: [items]
        vars: [id_purchase, id_layout]
    """

    from_purchase = False

    page_layout = None
    if request.vars.id_layout:
        page_layout = db.labels_page_layout(request.vars.id_layout)
    else:
        page_layout = db(db.labels_page_layout).select().first()
    if not page_layout:
        redirect(URL('labels_page_layout', 'index'))
    layout = Storage({
        'id': page_layout.id,
        'width': page_layout.id_paper_size.width,
        'height': page_layout.id_paper_size.height,
        'margin_top': page_layout.margin_top,
        'margin_right': page_layout.margin_right,
        'margin_bottom': page_layout.margin_bottom,
        'margin_left': page_layout.margin_left,
        'space_x': page_layout.space_x,
        'space_y': page_layout.space_y,
        'cols': page_layout.label_cols,
        'rows': page_layout.label_rows,
        'show_item_name': page_layout.show_name,
        'show_price': page_layout.show_price
    })

    layout.label_width = (layout.width - (layout.margin_left + layout.margin_right + layout.space_x * (layout.cols - 1))) / layout.cols
    layout.label_height = (layout.height - (layout.margin_top + layout.margin_bottom + layout.space_y * (layout.rows - 1))) / layout.rows

    if request.vars.id_purchase and request.vars.id_purchase != 'None':
        from_purchase = True
        purchase = db((db.purchase.id == request.vars.id_purchase) & (db.purchase.is_done == True)).select().first()
        if not purchase:
            raise HTTP(404)
        purchase_items = db(
            db.stock_item.id_purchase == purchase.id
        ).iterselect()
        if not purchase_items:
            raise HTTP(404)
        return dict(items=purchase_items, layout=layout)

    if request.args:
        items_ids = request.args(0).split('_')
        query = (db.item.id < 0)
        for item_id in items_ids:
            query |= (db.item.id == int(item_id))
        items = db(
            (query) & (db.item.is_active == True)
            & (db.item.has_inventory == True)
        ).select()

        return dict(items=items, layout=layout)

    redirect(URL('default', 'index'))

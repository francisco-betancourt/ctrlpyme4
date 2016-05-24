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
    categories_selected_text = item.categories_selected_text
    category_search = INPUT(_type="search", _id="category_search", _placeholder=T("search categories"), _class="form-control")
    categories_selected = INPUT(_value=categories_selected_text, _type="text", _id="categories_selected", _hidden=True, _name="categories_selected")
    # hack: this script sets the javascript variable categories_tree_data, to
    # the categories_tree json data, so it can be used inside the view.
    categories_tree_script = SCRIPT("categories_tree_data = %s;" % categories_tree)
    field = DIV(category_search, DIV(_id="categories_tree"), categories_selected, categories_tree_script, _class="col-sm-9")

    return DIV(LABEL(T('Categories'), _class="control-label col-sm-3"), field, _class="form-group")


def traits_tree(item_id=None, categories_ids=""):
    try:
        # we need a category in order to retrieve the traits
        if not categories_ids:
            return {}
        categories_ids = categories_ids.split(',')
        item = db.item(item_id)

        # select all the trait categories that are associated with a category in categories_ids, then select all the traits that are associated with the obtained trait categories
        query = (db.category.id < 0)
        for category_id in categories_ids:
            if category_id:
                query |= (db.category.id == category_id)
        categories = db(query).select()
        query = (db.trait.id < 0)
        for category in categories:
            query |= (db.trait.id_trait_category == category.trait_category1)
            query |= (db.trait.id_trait_category == category.trait_category2)
            query |= (db.trait.id_trait_category == category.trait_category3)
        traits = db(query & (db.trait.is_active == True)
                    ).select(orderby=db.trait.id_trait_category)
        # creates the trait tree
        trait_tree = []
        if not traits:
            return {}
        current_trait_category = traits.first().id_trait_category
        current_subtree = {"text": current_trait_category.name, "nodes": [], "selectable":False}
        for trait in traits:
            if trait.id_trait_category != current_trait_category:
                trait_tree.append(current_subtree)
                current_trait_category = trait.id_trait_category
                current_subtree = {"text": current_trait_category.name, "nodes": [], "selectable": False}
            node = {"text": trait.trait_option, "trait_id": trait.id}
            if item:
                if trait.id in item.traits:
                    node['state'] = {'selected': True}
            current_subtree['nodes'].append(node)
        trait_tree.append(current_subtree)
        current_trait_category = trait.id_trait_category
        current_subtree = {"text": current_trait_category.name, "nodes": []}
        return trait_tree
    except:
        import traceback
        traceback.print_exc()


def trait_selector_data():
    """ treeview based on the selected categories, use this function as json

        args:
            item_id: the current item (only available on updates)
        vars:
            categories: list of categories (separated by comma)

    """

    try:
        traits = traits_tree(request.args(0), request.vars.categories)
        if not traits:
            return dict(status='no traits')
        return dict(traits=traits)
    except:
        import traceback
        traceback.print_exc()



def trait_selector_html():
    """ Returns the trait selector html, for the treeview function """
    return DIV(
                LABEL(T('Traits'), _class="control-label col-sm-3"),
                DIV(DIV(_id="traits_tree"),
                    INPUT(_type="text", _hidden=True, _id="traits_selected", _name="traits_selected"),
                    _class="col-sm-9"
                ),
                _class="form-group"
            )


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
    categories = db((db.category.is_active==True) ).select(orderby=~db.category.parent)
    if categories:
        form[0].insert(4, categories_tree_html(categories, item))
        form[0].insert(5, trait_selector_html())

    if form.process().accepted:
        # categories
        form.vars.categories_selected
        l_categories = []
        for c in (form.vars.categories_selected or '').split(','):
            if not c:
                continue
            l_categories.append(int(c))
        # add the traits
        traits = [int(trait) for trait in form.vars.traits_selected.split(',')] if form.vars.traits_selected else None

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
            # redirect(URL('index'))
    elif form.errors:
        response.flash = 'form has errors'
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
    scan_form = SQLFORM.factory(
        Field('scan_code'), buttons=[], _id="scan_form"
    )
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
            item_id, item_qty = pair.split(':')
            db.bundle_item.update_or_insert((db.bundle_item.id_bundle == bundle.id) & (db.bundle_item.id_item == item_id), quantity=item_qty, id_bundle=bundle.id, id_item=item_id)
        redirect(URL('index'))
        response.flash = 'form accepted'
    elif form.errors:
        response.flash = 'form has errors'
    else:
        response.flash = 'please fill the form'

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


def get_by_brand():
    """
        args:
            id_brand
        vars: [page, ipp]
    """

    brand = db.brand(request.args(0))
    if not brand:
        raise HTTP(404)
    query = ((db.item.id_brand == brand.id) & (db.item.is_active == True))
    pages, limits = pages_menu(query, request.vars.page, request.vars.ipp, distinct=db.item.name)
    items = db(query).select(orderby=db.item.name, limitby=limits)

    return locals();


def get_item():
    """
        get the item specified by its id or name and traits
        args [item_id]
        vars {name, traits}
    """

    same_traits = False
    multiple_items = False
    query = (db.item.id == request.args(0))
    if not auth.is_logged_in() or (auth.user and auth.user.is_client):
        query &= db.item.is_active == True
    item = db(query).select().first()
    if not item:
        item_name = request.vars.name

        # when traits are specified, only one item with the specified name and traits should match
        # this is the first item
        item = None
        if request.vars.traits:
            traits = request.vars.traits.split(',')
            item = db(
                (db.item.name == item_name)
              & (db.item.traits.contains(traits, all=True))
              & (db.item.is_active == True)
            ).select().first()
        else:
            item = db(
                (db.item.name == item_name)
              & (db.item.is_active == True)
            ).select().first()
        if not item:
            raise HTTP(404)

        # since the could be multiple items with the same name, we query all the items with the specified name different than the first item
        items = db(
            (db.item.name == item_name)
          & (db.item.id != item.id)
          & (db.item.is_active == True)
        ).select()
        if items > 1:
            multiple_items = True

        same_traits = True
        base_trait_category_set = []
        trait_options = {}

        if multiple_items and item.traits:
            other_items = items
            for trait in item.traits:
                base_trait_category_set.append(trait.id_trait_category)
                trait_options[str(trait.id_trait_category.id)] = {
                    'id': trait.id_trait_category.id,
                    'options': [{'name': trait.trait_option, 'id': trait.id}]
                }
            base_trait_category_set = set(base_trait_category_set)
            # check if all the items have the same traits
            broken = False
            for other_item in other_items:
                other_trait_category_set = []
                if not other_item.traits and item.traits:
                    same_traits = False
                    break
                for trait in other_item.traits:
                    other_trait_category_set.append(trait.id_trait_category)
                    if not trait.id_trait_category in base_trait_category_set:
                        same_traits = False
                        broken = True
                        break
                    trait_options[str(trait.id_trait_category.id)]['options'].append({'name': trait.trait_option, 'id': trait.id})
                if broken:
                    break
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

    return locals()


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
        vars: {category, sort, categories, is_service}
    """

    category = db.category(request.vars.category)
    is_service = request.vars.is_service == 'yes'

    title = T('Items')

    query = (db.item.is_active == True)

    if category:
        query &= db.item.categories.contains(category.id)
    if is_service:
        title = T('Services')
        query &= db.item.has_inventory == False

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
    layout = {
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
    }

    layout = Storage(layout)
    layout.label_width = (layout.width - (layout.margin_left + layout.margin_right + layout.space_x * (layout.cols - 1))) / layout.cols
    layout.label_height = (layout.height - (layout.margin_top + layout.margin_bottom + layout.space_y * (layout.rows - 1))) / layout.rows

    if request.vars.id_purchase and request.vars.id_purchase != 'None':
        from_purchase = True
        purchase = db((db.purchase.id == request.vars.id_purchase) & (db.purchase.is_done == True)).select().first()
        if not purchase:
            raise HTTP(404)
        purchase_items = db(db.stock_item.id_purchase == purchase.id).select()
        if not purchase_items:
            raise HTTP(404)
        return dict(items=purchase_items, layout=layout)

    items_ids = request.args(0).split('_')
    query = (db.item.id < 0)
    for item_id in items_ids:
        query |= (db.item.id == int(item_id))
    items = db((query) & (db.item.is_active == True) & (db.item.has_inventory == True)).select()

    return dict(items=items, layout=layout)

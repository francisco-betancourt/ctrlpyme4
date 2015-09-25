# -*- coding: utf-8 -*-
#
# Author: Daniel J. Ramirez

import json


def categories_tree_html(categories, item=None):
    current_category = categories.first().parent
    categories_children = {}
    current_tree = []
    for category in categories:
        if category.parent != current_category:
            categories_children[current_category] = current_tree
            current_tree = []
            current_category = category.parent
        # current_tree.append({'text': category.name})
        child = {'text': category.name, 'category_id': category.id}
        if item:
            if category.id in item.categories:
                child['state'] = {'checked': True};
        if categories_children.has_key(category.id):
            child['nodes'] = categories_children[category.id]
            current_tree.append(child)
            if category.parent:
                del categories_children[category.id]
        else:
            current_tree.append(child)
    categories_children[current_category] = current_tree
    current_tree = []
    # the categories_children array contains the master categories.
    categories_tree = []
    for subtree in categories_children.itervalues():
        categories_tree.append(subtree)
    # json object from python dict
    categories_tree = json.dumps(categories_tree[0])
    category_search = INPUT(_type="search", _id="category_search", _placeholder=T("search categories"), _class="form-control")
    categories_selected = INPUT(_type="text", _id="categories_selected", _hidden=True, _name="categories_selected")
    # hack: this script sets the javascript variable categories_tree_data, to
    # the categories_tree json data, so it can be used inside the view.
    categories_tree_script = SCRIPT("categories_tree_data = %s;" % categories_tree)
    field = DIV(category_search, DIV(_id="categories_tree"), categories_selected, categories_tree_script, _class="col-sm-9")

    return DIV(LABEL(T('Categories'), _class="control-label col-sm-3"), field, _class="form-group")


def trait_selector_data():
    """ treeview based on the selected categories, use this function as json

        args:
            item_id: the current item (only available on updates)
        vars:
            categories: list of categories (separated by comma)

    """

    categories_ids = request.vars.categories
    if not categories_ids:
        return dict(status=1)
    categories_ids = categories_ids.split(',')
    item = db.item(request.args(0))

    # select all the trait categories that are associated with a category in categories_ids, then select all the traits that are associated with the obtained trait categories
    query = (db.category.id < 0)
    for category_id in categories_ids:
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
    return dict(traits=trait_tree)


def trait_selector_html():
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

    form = SQLFORM(db.item, item, showid=False, fields=['name', 'description', 'has_inventory', 'base_price', 'id_measure_unit', 'taxes', 'allow_fractions', 'reward_points'])

    # brand
    field = SELECT(OPTION(""), _name='id_brand', _class="form-control")
    brands = db(db.brand.id > 0).select()
    for brand in brands:
        field.append(OPTION(brand.name))
    # form_fields.append(field)
    form[0].insert(0, DIV(LABEL(T('Brand'), _class="control-label col-sm-3"), DIV(field, _class="col-sm-9"), _class="form-group"))

    # categories
    categories = db((db.category.id > 0) &
                    (db.category.is_active==True)
                   ).select(orderby=~db.category.parent)
    if categories:
        # form.vars.categories_selected
        form[0].insert(1, categories_tree_html(categories, item))
        # form.vars.traits_selected
        form[0].insert(2, trait_selector_html())

    if form.process().accepted:
        # categories
        categories = [int(c) for c in form.vars.categories_selected.split(',')] if form.vars.categories_selected else None
        # add the traits
        traits = [int(trait) for trait in form.vars.traits_selected.split(',')] if form.vars.traits_selected else None

        url_name = "%s%s" % (urlify_string(form.vars.name), form.vars.id)
        db.item(form.vars.id).update_record(url_name=url_name, is_bundle=is_bundle, traits=traits, categories=categories)
        response.flash = T('Item created')
        # if the item is bundle, redirect to the bundle filling page
        if is_bundle:
            redirect(URL('fill_bundle', args=form.vars.id))
        else:
            redirect(URL('index'))
    elif form.errors:
        response.flash = 'form has errors'
    return form


def create():
    """
        vars:
            is_bundle: whether the newly created item will be a bundle or not
    """

    form = item_form(is_bundle=is_bundle)

    return dict(form=form)


def create_or_update():
    """
        args:
            item: if this argument is present, then this function will return an update form
        vars:
            is_bundle: whether the newly created item will be a bundle or not
    """

    item = db.item(request.args(0))
    is_bundle = request.vars.is_bundle
    form = item_form(item=item, is_bundle=is_bundle)

    return locals()


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
            print item_qty
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
    item = db.item(request.args(0))
    if not item:
        raise HTTP(404)
    return locals()


def find_by_code():
    """
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


def update():
    """
        vars:
            is_bundle: whether the newly created item will be a bundle or not
    """

    # item = db.item(request.args(0))
    # if not item:
    #     raise HTTP(404)
    # is_bundle = request.vars.is_bundle
    # form = item_form(item=item, is_bundle=is_bundle)
    redirect(URL('create_or_update', args=request.args, vars=request.vars))

    # return locals()


def delete():
    return common_delete('item', request.args)


def index():
    rows = common_index('item')
    return locals()


def bundles_index():
    """ Return all the active bundle items  """

    rows = db((db.item.is_bundle == True) & (db.item.is_active == True)).select()
    return locals()

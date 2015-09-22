# -*- coding: utf-8 -*-
#
# Author: Daniel J. Ramirez

import json


def categories_tree_html(categories):
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

        vars:
            categories: list of categories (separated by comma)

    """

    categories_ids = request.vars.categories
    if not categories_ids:
        return dict(status=1)
    categories_ids = categories_ids.split(',')

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
               LABEL(T('Bundle items'), _class="control-label col-sm-3"),
               DIV(
                   INPUT(_id="bundle_item_code", _class="form-control",
                         _placeholder=T("Scan code..."))
                   , DIV(_id='bundle_items_list', _class="list-group")
                   , INPUT(_id="bundle_items_ids", _name="bundle_items_ids"
                           , _hidden=True)
                   , _id="bundle_items_form_group", _class="col-sm-9"
               )
               , _class="form-group", _id="bundle_items_form_group"
               , _hidden=True
           )


def create():

    form = SQLFORM(db.item, fields=['name', 'description', 'has_inventory', 'base_price', 'id_measure_unit', 'taxes', 'allow_fractions', 'reward_points'])

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
        form[0].insert(1, categories_tree_html(categories))
        form[0].insert(2, trait_selector_html())

    # form[0].insert(6, bundle_items_html())

    if form.process().accepted:
        url_name = "%s%s" % (urlify_string(form.vars.name), form.vars.id)
        db.item(form.vars.id).update_record(url_name=url_name)
        response.flash = 'form accepted'
    elif form.errors:
        response.flash = 'form has errors'
    return dict(form=form)


def get():
    pass


def update():
    return common_update('item', request.args)


def delete():
    return common_delete('item', request.args)


def index():
    rows = common_index('item')
    return locals()

# -*- coding: utf-8 -*-
#
# Author: Daniel J. Ramirez

import json


def create():

    form = SQLFORM(db.category, fields=['name', 'description'])

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
    current_category = categories.first().parent
    current_tree = []
    categories_children = {}
    for category in categories:
        if category.parent != current_category:
            # current_tree = [{"text": current_category, 'nodes': current_tree}]
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
    form[0].insert(1, DIV(LABEL(T('Categories'), _class="control-label col-sm-3"), field, _class="form-group"))

    if form.process().accepted:
        print form.vars
        response.flash = 'form accepted'
    elif form.errors:
        response.flash = 'form has errors'
    return dict(form=form)


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

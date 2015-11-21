# -*- coding: utf-8 -*-
#
# Author: Daniel J. Ramirez

def search_item():
    """
        args: [search_term]
        vars: {id_category}
    """

    category = db.category(request.vars.id_category)

    prettify = request.vars.pretty == 'True'

    term = request.args(0)

    # search by item name
    query = (db.item.name.contains(term))
    query |= (db.item.sku.contains(term))
    query |= (db.item.ean.contains(term))
    query |= (db.item.upc.contains(term))

    categories_data_script = SCRIPT()
    if not category:
        matched_categories = db(db.category.name.contains(term)).select()
        if matched_categories:
            matched_categories_ids = []
            for matched_category in matched_categories:
                matched_categories_ids.append(str(matched_category.id))
            # search by category
            query |= (db.item.categories.contains(matched_categories_ids, all=False))
    # else:
    #     query &= (db.item.categories.contains(category.id))
    #     categories_data_script = SCRIPT('var categories_tree_data = %s;' % json_categories_tree(None, visible_categories=[category.id]))


    # search by Brands
    matched_brands = db(db.brand.name.contains(term)).select()
    for matched_brand in matched_brands:
        query |= (db.item.id_brand == matched_brand.id)

    # search by trait
    matched_traits = [str(i['id']) for i in db(db.trait.trait_option.contains(term)).select(db.trait.id).as_list()]
    if matched_traits:
        query |= (db.item.traits.contains(matched_traits, all=False))

    query &= (db.item.is_active == True)

    items = db(query).select()

    return dict(items=items, categories_data_script=categories_data_script)

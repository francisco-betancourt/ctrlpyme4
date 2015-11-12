# -*- coding: utf-8 -*-
#
# Author: Daniel J. Ramirez

import json


@auth.requires_membership('Inventories')
def create():
    is_partial = bool(request.vars.is_partial or True)
    print is_partial
    id_inventory = db.inventory.insert(id_store=session.store, is_partial=is_partial, is_done=False)
    redirect(URL('fill', args=id_inventory, vars={'is_partial': is_partial}))
    if is_partial:
        redirect(URL('fill', args=id_inventory, vars={'is_partial': True}))
    else:
        redirect(URL('fill', args=id_inventory, vars={'is_partial': False}))


@auth.requires_membership('Inventories')
def fill():
    """
        args:
            id_inventory
        vars:
            is_partial
    """

    inventory = db.inventory(request.args(0))
    is_partial = bool(request.vars.is_partial)
    if not inventory:
        raise HTTP(404)

    json_inventory_items = []
    inventory_items = db(db.inventory_item.id_inventory == inventory.id).select()
    for inventory_item in inventory_items:
        json_inventory_item = {
              "id": inventory_item.id
            , "physical_qty": inventory_item.physical_qty
            , "id_item": {
                "id": inventory_item.id_item.id,
                "name": inventory_item.id_item.name
            }
            , "system_qty": inventory_item.system_qty
        }
        json_inventory_items.append(json_inventory_item)
    inventory_items_script = SCRIPT('var inventory_items = %s' % json.dumps(json_inventory_items))

    return locals()


@auth.requires_membership('Inventories')
def partial_inventory():
    """
        args:
            id_inventory
    """

    inventory = db.inventory(request.args(0))
    if not inventory:
        raise HTTP(404)



    return locals()


@auth.requires_membership('Inventories')
def full_inventory():
    return dict()


@auth.requires_membership('Inventories')
def modify_item():
    """
        args
            id_inventory_item
        vars:
            physical_qty
    """

    inventory_item = db.inventory_item(request.args(0))
    if not inventory_item:
        raise HTTP(404)
    try:
        inventory_item.physical_qty = fix_item_quantity(inventory_item.id_item, DQ(request.vars.physical_qty, True))
        inventory_item.update_record()
        return locals()
    except:
        import traceback
        traceback.print_exc()


@auth.requires_membership('Inventories')
def add_item():
    """
        args
            id_inventory
            id_item
    """

    inventory = db.inventory(request.args(0))
    item = db.item(request.args(1))
    if not inventory or not item:
        raise HTTP(404)
    if not item.has_inventory:
        raise HTTP(400)

    stocks, stock_qty = item_stock(item, session.store).itervalues()

    # check if theres an inventory item
    inventory_item = db((db.inventory_item.id_inventory == inventory.id)
                      & (db.inventory_item.id_item == item.id)
                       ).select().first()
    if not inventory_item:
        inventory_item = db.inventory_item.insert(id_item=item.id, id_inventory=inventory.id, system_qty=stock_qty, physical_qty=stock_qty)
        inventory_item = db.inventory_item(inventory_item)
    else:
        inventory_item.physical_qty += 1
        inventory_item.update_record()

    return dict(inventory_item=inventory_item, item=item)


@auth.requires_membership('Inventories')
def get():
    pass


@auth.requires_membership('Inventories')
def update():
    redirect(URL('fill', args=request.args, vars=request.vars))


# def delete():
#     return common_delete('inventory', request.args)


@auth.requires_membership('Inventories')
def index():
    rows = common_index('inventory')
    data = super_table('inventory', ['is_partial', 'is_done'], rows)
    return locals()

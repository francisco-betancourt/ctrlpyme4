# -*- coding: utf-8 -*-
#
# Author: Daniel J. Ramirez

import json


@auth.requires_membership('Inventories')
def create():
    is_partial = bool(request.vars.is_partial == 'True')
    id_inventory = db.inventory.insert(id_store=session.store, is_partial=is_partial, is_done=False)
    redirect(URL('fill', args=id_inventory))


@auth.requires_membership('Inventories')
def fill():
    """
        args:
            id_inventory
    """

    inventory = db.inventory(request.args(0))
    is_partial = inventory.is_partial
    if not inventory:
        raise HTTP(404)
    if inventory.is_done:
        raise HTTP(405, "Inventory is done")

    # we use this list to send the inventory items in json format to the client, so it can rebuild the inventory items list
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
def modify_item():
    """ Allows the modification of the physical quantity
        args
            id_inventory_item
        vars:
            physical_qty
    """

    inventory_item = db.inventory_item(request.args(0))
    if not inventory_item:
        raise HTTP(404)
    if inventory_item.id_inventory.is_done:
        raise HTTP(405, "Inventory is done")
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
    if inventory.is_done:
        raise HTTP(405, "Inventory is done")
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


def partial_inventory_check(inventory):
    """ Given the inventory items, fix the current system stocks to match the physical quantities """

    inventory_items = db(db.inventory_item.id_inventory == inventory.id).select()

    for inventory_item in inventory_items:
        diff = inventory_item.system_qty - inventory_item.physical_qty
        # more system stock than actual physical stock
        if diff > 0:
            # remove items from the oldest stocks
            remainder = diff
            stock_items = item_stock(inventory_item.id_item, session.store)['stocks']
            #TODO check the case when after iterating over all the stock items, we still have remainder, which will be very unlikely to happen
            for stock_item in stock_items:
                if remainder <= 0:
                    # exit once we have removed all the physical stock items
                    break
                remaining_stock = stock_item.stock_qty
                removed_from_stock = min(remaining_stock, remainder)
                stock_item.stock_qty -= removed_from_stock
                remainder -= removed_from_stock
                stock_item.update_record()

        # more physical stock than system stock
        elif diff < 0:
            # avg item purchase_price
            avg = db.stock_item.price.avg()
            avg_item_price = 0
            last_inventory = db(db.inventory.id != inventory.id).select().last()
            if last_inventory:
                # the average price is based on the items obtained after the last inventory
                last_inventory_date = last_inventory.modified_on
                avg_item_price = db(
                    (db.stock_item.id_store == session.store)
                    & (db.stock_item.id_item == inventory_item.id_item.id)
                    & (db.stock_item.created_on > last_inventory_date)
                ).select(avg).first()[avg]
            else:
                # the average price is based on all the obtained items
                avg_item_price = db(
                    (db.stock_item.id_store == session.store)
                    & (db.stock_item.id_item == inventory_item.id_item.id)
                ).select(avg).first()[avg]
            #  add items to an inventory stock
            db.stock_item.insert(
                id_item=inventory_item.id_item.id
                , purchase_qty=DQ(abs(diff))
                , stock_qty=DQ(abs(diff))
                , price=avg_item_price
                , taxes=0 # we do not consider taxes
                , id_inventory=inventory_item.id_inventory.id
                , id_store=session.store
            )
    return inventory_items


def full_inventory_check(inventory):
    missing_items = []

    inventory_items = partial_inventory_check(inventory)
    all_items_with_inventory = db(
        (db.item.has_inventory == True)
        & (db.item.is_active == True)
    ).select()

    #TODO this is ugly, check if theres is a better way to do it
    for item in all_items_with_inventory:
        inventory_item = db(
            (db.inventory_item.id_item == item.id)
            & (db.inventory_item.id_inventory == inventory.id)
        ).select().first()
        # if the item is not in the inventory, then we have to report it as a missing item
        if not inventory_item:
            missing_items.append(item)
    # we have to create an inventory item for every missing item, setting the total stock quantoty to 0
    missing_items_count = 0
    for missing_item in missing_items:
        print missing_item
        stock_items, quantity = item_stock(missing_item, session.store).itervalues()
        # when there are no stocks, never purhcased.
        if not stock_items:
            continue
        remainder = quantity
        #TODO check the case when after iterating over all the stock items, we still have remainder, which will be very unlikely to happen
        for stock_item in stock_items:
            if remainder <= 0:
                # exit once we have removed all the physical stock items
                break
            remaining_stock = stock_item.stock_qty
            removed_from_stock = min(remaining_stock, remainder)
            stock_item.stock_qty -= removed_from_stock
            remainder -= removed_from_stock
            stock_item.update_record()
        # create a missing inventory item
        db.inventory_item.insert(
            id_inventory=inventory.id
            , id_item=missing_item.id
            , system_qty=quantity
            , physical_qty=0
            , is_missing=True
        )
        missing_items_count += 1

    return missing_items_count


@auth.requires_membership('Inventories')
def complete():
    """
        args:
            id_inventory
    """

    inventory = db.inventory(request.args(0))
    if inventory.is_done:
        raise HTTP(405, "Inventory is done")
    if not inventory:
        raise HTTP(404)

    missing_items = None
    try:
        if inventory.is_partial:
            partial_inventory_check(inventory)
        else:
            missing_items_count = full_inventory_check(inventory)
    except:
        import traceback
        traceback.print_exc()

    inventory.is_done = True
    inventory.update_record()

    if inventory.is_partial:
        redirect(URL('index'))
    else:
        if missing_items_count:
            redirect(URL('report_missing_items', args=inventory.id))
        else:
            redirect(URL('index'))

@auth.requires_membership('Inventories')
def report_missing_items():
    """
        args:
            id_inventory
    """

    inventory = db.inventory(request.args(0))
    if not inventory:
        raise HTTP(404)
    if not inventory.is_done:
        raise HTTP(405, T("Inventory has not been applied"))
    missing_items = db(
        (db.inventory_item.is_missing == True)
        & (db.inventory_item.id_inventory == inventory.id)
        ).select()
    return locals()


@auth.requires_membership('Inventories')
def undo():
    """
        args
            id_inventory
    """

    inventory = db.inventory(request.args(0))
    if not inventory:
        raise HTTP(404)
    if not inventory.is_done:
        raise HTTP(405, T("Inventory has not been applied"))


def inventory_options(row):
    td = TD()
    # edit option
    if not row.is_done:
        td.append(option_btn('pencil', URL('fill', args=row.id)))
    td.append(option_btn('eye-slash', onclick='delete_rows("/%s", "", "")' % (row.id)))
    return td


@auth.requires_membership('Inventories')
def index():
    rows = db(db.inventory.is_active == True).select(orderby=~db.inventory.id)
    data = super_table('inventory', ['is_partial', 'is_done'], rows, options_function=inventory_options, show_id=True)
    return locals()
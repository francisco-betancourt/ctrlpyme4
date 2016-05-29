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

precheck()

import json

from item_utils import active_item, _remove_stocks, undo_stock_removal


def is_valid_inventory(inventory):
    if not inventory:
        raise HTTP(404)
    if inventory.is_done:
        raise HTTP(405, T("Inventory is done"))
    return True


#TODO avoid inventory if there are pending sales
@auth.requires_membership('Inventories')
def create():
    is_partial = bool(request.vars.is_partial == 'True')
    id_inventory = db.inventory.insert(id_store=session.store, is_partial=is_partial, is_done=False)
    redirect(URL('fill', args=id_inventory))


@auth.requires_membership('Inventories')
def fill():
    """ args [ id_inventory ] """

    inventory = db.inventory(request.args(0))
    is_partial = inventory.is_partial
    is_valid_inventory(inventory)

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
        args [ id_inventory_item ]
        vars: [ physical_qty ]
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
        args [id_inventory, id_item]
    """

    inventory = db.inventory(request.args(0))
    if inventory.is_done:
        raise HTTP(405, T("Inventory is done"))
    item = active_item(request.args(1))
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
    """ inventory details
        args [ id_inventory ]
    """

    inventory = db.inventory(request.args(0))
    if not inventory.is_done:
        raise HTTP(405, T("Inventory is not done"))
    inventory_items = db(db.inventory_item.id_inventory == inventory.id).select()

    return locals()


@auth.requires_membership('Inventories')
def update():
    redirect(URL('fill', args=request.args, vars=request.vars))


def partial_inventory_check(inventory):
    """ Given the inventory items, fix the current system stocks to match the physical quantities """

    inventory_items = db(db.inventory_item.id_inventory == inventory.id).select()

    for inventory_item in inventory_items:
        diff = inventory_item.system_qty - inventory_item.physical_qty
        # more system stock than actual physical stock (missing items)
        if diff > 0:
            _remove_stocks(inventory_item.id_item, diff, request.now, inventory_item=inventory_item
            )

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
    """ Checks all the inventory items and report items that were missed after the inventory
    """

    partial_inventory_check(inventory)

    # get all the items that does not have inventory item
    missing_items = db(
        (db.item.has_inventory == True)
        & (db.item.is_active == True)
        & (db.inventory.id == inventory.id)
        & (db.inventory_item.id_item == None)
    ).select(db.item.ALL, left=db.inventory_item.on(
            (db.item.id == db.inventory_item.id_item)
            & (db.inventory.id == db.inventory_item.id_inventory)
        )
    )

    # we have to create an inventory item for every missing item, setting the total stock quantoty to 0
    missing_items_count = 0
    for missing_item in missing_items:
        # TODO this could use _remove_stocks()
        stock_items, quantity = item_stock(missing_item, session.store).itervalues()
        # when there are no stocks (never purchased).
        if not stock_items:
            continue

        remainder = quantity
        # create a missing inventory item
        new_inventory_item_id = db.inventory_item.insert(
            id_inventory=inventory.id
            , id_item=missing_item.id
            , system_qty=quantity
            , physical_qty=0
            , is_missing=True
        )
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

            db.stock_item_removal.insert(
                id_stock_item=stock_item.id,
                qty=removed_from_stock,
                id_inventory_item=new_inventory_item_id,
                id_inventory=inventory.id,
                id_item=stock_item.id_item.id
            )
        missing_items_count += 1

    return missing_items_count


@auth.requires_membership('Inventories')
def complete():
    """
        args: [id_inventory]
    """

    inventory = db.inventory(request.args(0))
    if inventory.is_done:
        raise HTTP(405, T("Inventory is already done"))
    if not inventory:
        raise HTTP(404, T("Inventory not found"))

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
    """ args: [id_inventory] """

    inventory = db.inventory(request.args(0))
    if not inventory:
        raise HTTP(404, T('Inventory not found'))
    if not inventory.is_done:
        raise HTTP(405, T("Inventory has not been applied"))
    query = (db.inventory_item.is_missing == True) & (db.inventory_item.id_inventory == inventory.id)
    data = SUPERT(query, fields=[
            'id_item.name',
            dict(
                fields=['id_item.sku'], label_as='barcode',
                custom_format=lambda r, f : item_barcode(r.id_item)
            )
        ]
        , options_enabled=False
        , global_options=[]
        , searchable=False
    )
    return locals()


@auth.requires_membership('Inventories')
def undo():
    """ Removes the last inventory, and restocks items according to the last system quantities. this operation is available only when the stocks produced by the inventory haven't been used.
        args: [id_inventory]
    """

    inventory = db.inventory(request.args(0))
    if not inventory:
        session.flash = T("Inventory not found")
        redirect(URL('index', 'default'))
    if not inventory.is_done:
        session.flash = T("Inventory has not been applied")
        redirect(URL('index', 'default'))
    if inventory.created_by.id != auth.user.id:
        session.flash = T("Not your inventory")
        redirect(URL('index', 'default'))

    # remove the items that were added by the inventory
    stock_items = db( (db.stock_item.id_inventory == inventory.id) ).select()
    used = False
    for stock_item in stock_items:
        tainted &= stock_item.stock_qty == stock_item.purchase_qty
    if used:
        session.info = T('Inventory has been used, you can not undo it')
        redirect(URL('default', 'index'))
    # inventory not used, we can proceed
    # restore stocks for inventory items
    undo_stock_removal(inventory=inventory)

    session.info = T('Inventory undone')
    redirect(URL('default', 'index'))


def delete():
    """ deletes an inventory, only available if the inventory is not done """

    db((db.inventory.is_done == False) & (db.inventory.id == request.args(0))).delete()
    redirect(URL('index'))



def inventory_options(row):
    buttons = ()
    # edit option
    if not row.is_done:
        buttons += OPTION_BTN('edit', URL('fill', args=row.id), title=T('edit')),
        buttons += OPTION_BTN('delete', URL('delete', args=row.id), title=T('delete')),
    else:
        buttons += OPTION_BTN('undo', URL('undo', args=row.id), title=T('undo')),
        buttons += OPTION_BTN('assignment', URL('get', args=row.id), title=T('details')),
    return buttons


@auth.requires_membership('Inventories')
def index():
    data = common_index('inventory', ['is_partial', 'is_done', 'created_on'], dict(options_func=inventory_options, searchable=False, select_args=dict(orderby=~db.inventory.created_on), global_options=[]))
    return locals()

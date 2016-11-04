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

expiration_redirect()
precheck()

import json
import item_utils


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
    """ args [ id_inventory, id_inventory_item ] """

    import supert
    Supert = supert.Supert()

    inventory = db.inventory(request.args(0))
    is_partial = inventory.is_partial
    is_valid_inventory(inventory)

    def inventory_item_options(row):
        return supert.OPTION_BTN('edit', URL('fill', args=[inventory.id, row.id], vars=request.vars))

    inventory_item = None
    if request.args(1):
        inventory_item = db(
            (db.inventory_item.id == request.args(1))
            & (db.inventory_item.id_inventory == inventory.id)
        ).select().first()

    inventory_items_table = Supert.SUPERT(
        (db.inventory_item.id_inventory == inventory.id)
        , fields=['id_item.name', 'system_qty',
            dict(
                fields=['physical_qty'],
                label_as=T('Physical quantity'),
                custom_format=lambda r, f : SPAN(r[f[0]], _id='item_%s_%s' % (r.id, f[0]))
            )
        ]
        , options_func=inventory_item_options
        , global_options=[]
    )

    brands = db(db.brand.is_active == True).select(orderby=db.brand.name)

    return locals()



def add_inventory_item(inventory, item):
    stock_qty = item_stock_qty(item, session.store)

    # check if theres an inventory item
    inventory_item = db(
        (db.inventory_item.id_inventory == inventory.id)
      & (db.inventory_item.id_item == item.id)
    ).select().first()
    if not inventory_item:
        inventory_item = db.inventory_item.insert(id_item=item.id, id_inventory=inventory.id, system_qty=stock_qty, physical_qty=stock_qty)
        inventory_item = db.inventory_item(inventory_item)
    else:
        inventory_item.physical_qty += 1
        inventory_item.update_record()

    return inventory_item



@auth.requires_membership('Inventories')
def add_brand_items():
    """ Add all the items from the specified brand to the inventory
        args: [inventory_id, brand_id]
    """

    inventory = db.inventory(request.args(0))
    is_valid_inventory(inventory)
    brand = db.brand(request.args(1))

    if not brand:
        raise HTTP(404)

    brand_items = db(
        (db.item.id_brand == brand.id) &
        (db.item.is_active == True) &
        (db.item.has_inventory == True)
    ).iterselect(orderby=~db.item.id)

    for item in brand_items:
        add_inventory_item(inventory, item)

    return dict(status="ok")




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
def remove_item():
    """ Allows the modification of the physical quantity
        args [ id_inventory_item ]
    """

    inventory_item = db.inventory_item(request.args(0))
    if not inventory_item:
        raise HTTP(404)
    if inventory_item.id_inventory.is_done:
        raise HTTP(405, T("Inventory is done"))
    try:
        inventory_item.delete_record()
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
    item = item_utils.active_item(request.args(1))
    if not inventory or not item:
        raise HTTP(404)
    if not item.has_inventory or item.is_bundle:
        raise HTTP(400)

    inventory_item = add_inventory_item(inventory, item)

    return dict(inventory_item=inventory_item, item=item)


@auth.requires_membership('Inventories')
def get():
    """ inventory details
        args [ id_inventory ]
    """

    import supert
    Supert = supert.Supert()

    inventory = db.inventory(request.args(0))
    if not inventory.is_done:
        raise HTTP(405, T("Inventory is not done"))

    def physical_qty_format(row, f):
        diff = row.physical_qty - row.system_qty
        sgn = '-' if diff < 0 else '+'
        diff = B(' ( %s %s )' % (sgn, abs(diff)))
        if row.physical_qty == row.system_qty:
            return I(_class='status-circle accent-color'), SPAN(row[f[0]]),
        # lost items
        elif row.physical_qty < row.system_qty:
            return I(_class='status-circle bg-danger'), SPAN(row[f[0]]), diff,
        elif row.physical_qty > row.system_qty:
            return I(_class='status-circle bg-success'), SPAN(row[f[0]]), diff,


    missing_items_data = Supert.SUPERT(
        (db.inventory_item.id_inventory == inventory.id) &
        (db.inventory_item.is_missing == True)
        , fields=[
            'id_item.name',
            dict(
                fields=['id_item'],
                label_as=T('Barcode'),
                custom_format=lambda r, f : item_barcode(r[f[0]])
            ),
            'system_qty',
            dict(
                fields=['physical_qty'],
                label_as=T('Physical quantity'),
                custom_format=physical_qty_format
            )
        ]
        , options_enabled=False
        , global_options=[]
        , title=T('Items not reported')
    )

    data = Supert.SUPERT(
        (db.inventory_item.id_inventory == inventory.id) &
        (db.inventory_item.is_missing == False)
        , fields=[
            'id_item.name',
            dict(
                fields=['id_item'],
                label_as=T('Barcode'),
                custom_format=lambda r, f : item_barcode(r[f[0]])
            ),
            'system_qty',
            dict(
                fields=['physical_qty'],
                label_as=T('Physical quantity'),
                custom_format=physical_qty_format
            )
        ]
        , options_enabled=False
        , global_options=[]
    )

    return locals()


@auth.requires_membership('Inventories')
def update():
    redirect(URL('fill', args=request.args, vars=request.vars))


def partial_inventory_check(inventory):
    """ Given the inventory items, fix the current system stocks to match the physical quantities """

    inventory_items = db(db.inventory_item.id_inventory == inventory.id).iterselect()

    for inventory_item in inventory_items:
        diff = inventory_item.system_qty - inventory_item.physical_qty
        # more system stock than actual physical stock (missing items)
        if diff > 0:
            item_utils._remove_stocks(
                inventory_item.id_item, diff, request.now,
                inventory_item=inventory_item
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
                ).select(avg).first()[avg] or 0
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

    inventory_items = db(
        db.inventory_item.id_inventory == inventory.id
    )._select(db.inventory_item.id_item)

    # get the items with stock in the current store and were not reported in the inventory
    missing_items = db(
        (db.stock_item.id_store == session.store) &
        (db.stock_item.stock_qty > 0) &
        (~db.stock_item.id_item.belongs(inventory_items))
    ).iterselect(db.stock_item.id_item, groupby=db.stock_item.id_item)

    has_missing_items = False

    for stock_item in missing_items:
        has_missing_items = True

        missing_item = db.item(stock_item.id_item)

        quantity = item_stock_qty(missing_item, session.store)

        new_inventory_item_id = db.inventory_item(db.inventory_item.insert(
            id_inventory=inventory.id
            , id_item=missing_item.id
            , system_qty=quantity
            , physical_qty=0
            , is_missing=True
        ))

        item_utils._remove_stocks(
            missing_item, quantity, request.now,
            inventory_item=new_inventory_item_id
        )

    return has_missing_items



@auth.requires_membership('Inventories')
def complete():
    """
        args: [id_inventory]
    """

    inventory = db.inventory(request.args(0))
    if inventory.is_done:
        session.info = T("Inventory is already done")
        redirect(URL('default', 'index'))
    if not inventory:
        session.info = T("Inventory not found")
        redirect(URL('default', 'index'))

    if inventory.is_partial:
        partial_inventory_check(inventory)
    else:
        inventory.has_missing_items = full_inventory_check(inventory)

    inventory.is_done = True
    inventory.update_record()

    session.info = T('Inventory done, system stock fixed')
    redirect(URL('get', args=inventory.id))



@auth.requires_membership('Inventories')
def undo():
    """ Removes the last inventory, and restocks items according to the last system quantities. this operation is available only when the stocks produced by the inventory haven't been used (sold). The intended use of this action is to undo inventories commited by mistake (even though the commited inventory will be lost).
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
    used = not db(
        (db.stock_item.id_inventory == inventory.id) &
        (db.stock_item.stock_qty != db.stock_item.purchase_qty)
    ).isempty()

    # do not allow when the items introduced by an inventory has been sold
    if used:
        session.info = T('Inventory has been used, you can not undo it')
        redirect(URL('default', 'index'))
    # inventory not used, we can proceed
    # restore stocks for inventory items
    item_utils.undo_stock_removal(inventory=inventory, remove=False)

    inventory.is_done = False
    inventory.update_record()

    session.info = T('Inventory undone')
    redirect(URL('inventory', 'index'))


def delete():
    """ deletes an inventory, only available if the inventory is not done """

    db((db.inventory.is_done == False) & (db.inventory.id == request.args(0))).delete()
    redirect(URL('index'))



def inventory_options(row):
    import supert

    buttons = ()
    # edit option
    if not row.is_done:
        buttons += supert.OPTION_BTN('edit', URL('fill', args=row.id), title=T('edit')),
        buttons += supert.OPTION_BTN('delete', URL('delete', args=row.id), title=T('delete')),
    else:
        buttons += supert.OPTION_BTN('undo', URL('undo', args=row.id), title=T('undo')),
        buttons += supert.OPTION_BTN('assignment', URL('get', args=row.id), title=T('details')),
    return buttons


@auth.requires_membership('Inventories')
def index():
    data = common_index('inventory', ['id', 'is_partial', 'is_done', 'created_on'], dict(options_func=inventory_options, searchable=False, select_args=dict(orderby=~db.inventory.created_on), global_options=[]))
    return locals()

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


from decimal import Decimal as D
from decimal import ROUND_FLOOR
from math import floor
import bag_utils
from item_utils import item_stock_qty, discount_data, remove_stocks


allow_out_of_stock = True


@auth.requires_membership( 'Sales bags' )
def set_bag_service_performer():
    """
        modifies the bag_service performer.
        args: [ bag_item (service), id_user ]

    """

    bag_item = db.bag_item(request.args(0))
    bag_utils.is_modifiable_bag(bag_item.id_bag)
    if not bag_item or bag_item.id_item.has_inventory:
        raise HTTP(404)

    user = db.auth_user(request.args(1))
    if not user or user.is_client or user.registration_key != '':
        raise HTTP(404)

    bag_item.performed_by = user.id
    bag_item.update_record()

    return dict()



@auth.requires(auth.has_membership('Sales bags')
            or auth.has_membership('Clients')
            )
def modify_bag_item():
    """
        modifies the bag_item quantity.
        args: [ bag_item ]

    """

    bag_item = db.bag_item(request.args(0))
    bag_utils.is_modifiable_bag(bag_item.id_bag)
    if not bag_item:
        raise HTTP(404)

    old_qty = bag_item.quantity
    bag_item.quantity = request.vars.quantity if request.vars.quantity else bag_item.quantity
    if not bag_item.id_item.allow_fractions:
        bag_item.quantity = remove_fractions(bag_item.quantity)
    bag_item.quantity = DQ(bag_item.quantity)

    if not allow_out_of_stock:
        qty = item_stock_qty(db.item(bag_item.id_item), session.store, id_bag=session.current_bag)
        diff = (old_qty - bag_item.quantity) if (old_qty - bag_item.quantity) > 0 else 0
        if qty + diff < bag_item.quantity - old_qty:
            bag_item.quantity = max(old_qty, qty + old_qty)
    bag_item.quantity = max(0, bag_item.quantity)

    bag_item.update_record()
    bag_data = bag_utils.refresh_bag_data(bag_item.id_bag.id)
    return dict(status='ok', bag_item=bag_item, **bag_data)


@auth.requires(auth.has_membership('Sales bags')
            or auth.has_membership('Clients')
            )
@service.jsonrpc
@service.jsonrpc2
def select_bag():
    """ Set the specified bag as the current bag. The current bag will be available as session.current_bag

        args: [bag_id]
    """
    bag = None
    try:
        bag = bag_utils.is_modifiable_bag(request.args(0))
    except:
        bag = bag_utils.auto_bag_selection()
    if not bag:
        raise HTTP(404)
    session.current_bag = bag.id
    return bag_utils.bag_selection_return_format(bag)


@auth.requires(auth.has_membership('Sales bags')
            or auth.has_membership('Clients')
            )
def add_bag_item():
    """ Creates a bag item with id_item = id_item for the current session bag
        args: [ id_item ] """

    from cp_errors import CP_OutOfStockError

    item = db(
        (db.item.id == request.args(0)) & (db.item.is_active == True)
    ).select().first()

    bag = bag_utils.is_modifiable_bag(session.current_bag)
    id_bag = bag.id if bag else None
    if not item or not id_bag:
        raise HTTP(404)
    try:
        bag_item = bag_utils.add_bag_item(bag, item)

        bag_item = bag_utils.set_bag_item(bag_item)
        bag_data = bag_utils.refresh_bag_data(id_bag)

        return dict(bag_item=bag_item, **bag_data)
    except CP_OutOfStockError as e:
        return dict(status=e)


@auth.requires(auth.has_membership('Sales bags')
            or auth.has_membership('Clients')
            )
def delete_bag_item():
    """
        args:[ id_bag_item]
    """

    bag_item = db.bag_item(request.args(0))

    if not bag_item:
        raise HTTP(404)

    bag_utils.is_modifiable_bag(bag_item.id_bag)
    db(db.bag_item.id == request.args(0)).delete()
    bag_data = bag_utils.refresh_bag_data(bag_item.id_bag.id)
    return dict(status="ok", **bag_data)


@auth.requires_membership('Sales bags')
def discard_bag():
    bag = bag_utils.is_modifiable_bag(session.current_bag)
    removed_bag = session.current_bag
    db(db.bag_item.id_bag == bag.id).delete()
    db(db.bag.id == bag.id).delete()

    bag_utils.auto_bag_selection()

    return dict(other_bag=db.bag(session.current_bag), removed=removed_bag)


@auth.requires_membership('Sales bags')
def change_bag_item_sale_price():
    price_index = request.args(0)
    bag_item = db.bag_item(request.args(1))
    access_code = request.args(2)

    access = False
    if auth.has_membership('Admin') or auth.has_membership('Manager'):
        access = True
    if not (price_index or bag_item or access_code or access):
        raise HTTP(400)
    bag_utils.is_modifiable_bag(bag_item.id_bag)
    user = db((db.auth_user.access_code == access_code)).select().first() if access_code else None
    is_vip_seller = auth.has_membership(None, user.id, role='VIP seller') or auth.has_membership(None, user.id, role='Admin') or auth.has_membership(None, user.id, role='Manager') if user else access
    if is_vip_seller:
        # change the item bag item sale price in db
        sale_price = bag_item.sale_price
        discount_p = D(1) - (sale_price / (sale_price + bag_item.discount))
        if price_index == '1':
            sale_price = bag_item.id_item.base_price
        elif price_index == '2':
            sale_price = bag_item.id_item.price2
        elif price_index == '3':
            sale_price = bag_item.id_item.price3
        bag_item.sale_price = sale_price - sale_price * discount_p
        bag_item.discount = sale_price * discount_p
        bag_item.sale_taxes = item_taxes(bag_item.id_item, bag_item.sale_price or 0)
        bag_item.update_record()
    else:
        raise HTTP(401)

    bag_data = refresh_bag_data(bag_item.id_bag.id)

    return dict(status="ok", **bag_data)


@auth.requires(auth.has_membership('Sales bags')
            or auth.has_membership('Clients')
            )
def complete():
    """ Check bag consistency and set its status based on the user role """

    from cp_errors import CP_EmptyBagError

    bag = bag_utils.is_modifiable_bag(session.current_bag)

    try:
        bag_utils.complete(bag)
        bag_utils.auto_bag_selection()

    except CP_EmptyBagError:
        bag_utils.auto_bag_selection()
        redirection()

    if auth.has_membership(None, bag.created_by.id, 'Clients'):
        redirect(URL('sale_order', 'create', args=bag.id))

    if auth.has_membership('Sales checkout'):
        redirect(URL('sale', 'create', args=bag.id))
    else:
        redirect(URL('ticket', args=bag.id))



@auth.requires_membership('Stock transfers')
def stock_transfer():
    """ """

    bag = bag_utils.is_modifiable_bag(session.current_bag)

    # check if all the bag items are consistent
    bag_items = db(db.bag_item.id_bag == bag.id).select()
    # delete the bag if there are no items
    if not bag_items:
        db(db.bag.id == bag.id).delete()
        bag_utils.auto_bag_selection()
        redirection()

    check_bag_items_integrity(bag_items)

    # create stock transfer record
    new_stock_transfer_id = db.stock_transfer.insert(id_store_from=bag.id_store.id, id_bag=bag.id)
    bag.status = BAG_COMPLETE
    bag.update_record()
    remove_stocks(bag_items)

    redirect(URL('stock_transfer', 'ticket', args=new_stock_transfer_id))


def ticket():
    """ args: [bag_id] """

    redirect( URL( 'ticket', 'get', vars=dict(id_bag=request.args(0)) ) )


@auth.requires(auth.has_membership('Sales checkout')
            or auth.has_membership('Admin')
            or auth.has_membership('Manager')
            )
def get():
    """ args: [bag_id] """

    bag = is_complete_bag(request.args(0))
    return dict(bag=bag)


@auth.requires_membership('Sales bags')
def create():
    """
    """

    try:
        id_bag = bag_utils.new(session.store, request.now, auth.user)
        session.current_bag = id_bag
        bag = db.bag(id_bag)

        return dict(bag=bag)
    except:
        import traceback
        traceback.print_exc()

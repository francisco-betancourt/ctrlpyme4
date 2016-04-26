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
from bag_utils import *
from item_utils import item_stock, discount_data


allow_out_of_stock = True


@auth.requires(auth.has_membership('Sales bags')
            or auth.has_membership('Clients')
            )
def modify_bag_item():
    """
        modifies the bag_item quantity.
        args: [ bag_item ]

    """

    bag_item = db.bag_item(request.args(0))
    is_modifiable_bag(bag_item.id_bag)
    if not bag_item:
        raise HTTP(404)

    old_qty = bag_item.quantity
    bag_item.quantity = request.vars.quantity if request.vars.quantity else bag_item.quantity
    if not bag_item.id_item.allow_fractions:
        bag_item.quantity = remove_fractions(bag_item.quantity)
    bag_item.quantity = DQ(bag_item.quantity)

    if not allow_out_of_stock:
        qty = item_stock(db.item(bag_item.id_item), session.store, id_bag=session.current_bag)['quantity']
        diff = (old_qty - bag_item.quantity) if (old_qty - bag_item.quantity) > 0 else 0
        if qty + diff < bag_item.quantity - old_qty:
            bag_item.quantity = max(old_qty, qty + old_qty)
    bag_item.quantity = max(0, bag_item.quantity)

    bag_item.update_record()
    bag_data = refresh_bag_data(bag_item.id_bag.id)
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
        bag = is_modifiable_bag(request.args(0))
    except:
        bag = auto_bag_selection()
    if not bag:
        raise HTTP(404)
    session.current_bag = bag.id
    return bag_selection_return_format(bag)


@auth.requires(auth.has_membership('Sales bags')
            or auth.has_membership('Clients')
            )
def add_bag_item():
    """ Creates a bag item with id_item = id_item for the current session bag
        args: [ id_item ] """

    item = db.item(request.args(0))
    bag = is_modifiable_bag(session.current_bag)
    id_bag = bag.id if bag else None
    if not item or not id_bag:
        raise HTTP(404)
    try:
        bag_item = db((db.bag_item.id_item == item.id)
                    & (db.bag_item.id_bag == id_bag)
                    ).select().first()

        item_stock_qty = item_stock(item, session.store, id_bag=session.current_bag)['quantity']
        if item.has_inventory:
            item_stock_qty = DQ(item_stock_qty)
        base_qty = base_qty = 1 if item_stock_qty >= 1 or allow_out_of_stock else item_stock_qty % 1 # modulo to consider fractionary items
        # if there is no stock notify the user
        if base_qty <= 0:
            return dict(status="out of stock")

        # create item taxes string, the string contains the tax name and its percentage, see db.py > bag_item table for more info
        if not bag_item:
            item_taxes_str = ''
            for tax in item.taxes:
                item_taxes_str += '%s:%s' % (tax.name, tax.percentage)
                if tax != item.taxes[-1]:
                    item_taxes_str += ','
            discounts = item_discounts(item)
            sale_price = discount_data(discounts, item.base_price)[0]
            discount = item.base_price - sale_price
            id_bag_item = db.bag_item.insert(id_bag=id_bag, id_item=item.id, quantity=base_qty, sale_price=sale_price, discount=discount, product_name=item.name, item_taxes=item_taxes_str,
                sale_taxes=item_taxes(item, sale_price))
            bag_item = db.bag_item(id_bag_item)
        else:
            bag_item.quantity += base_qty
            bag_item.update_record()

        bag_item = set_bag_item(bag_item)
        bag_data = refresh_bag_data(id_bag)

        return dict(bag_item=bag_item, **bag_data)
    except:
        import traceback
        traceback.print_exc()


@auth.requires(auth.has_membership('Sales bags')
            or auth.has_membership('Clients')
            )
def delete_bag_item():
    """
        args:
            id_bag_item
    """

    bag_item = db.bag_item(request.args(0))
    is_modifiable_bag(bag_item.id_bag)
    db(db.bag_item.id == request.args(0)).delete()
    bag_data = refresh_bag_data(bag_item.id_bag.id)
    return dict(status="ok", **bag_data)


@auth.requires_membership('Sales bags')
def discard_bag():
    bag = is_modifiable_bag(session.current_bag)
    removed_bag = session.current_bag
    db(db.bag_item.id_bag == bag.id).delete()
    db(db.bag.id == bag.id).delete()

    auto_bag_selection()

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
    is_modifiable_bag(bag_item.id_bag)
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
    """ Check bag consistency and set the its status based on the user role """

    bag = is_modifiable_bag(session.current_bag)

    # check if all the bag items are consistent
    bag_items = db(db.bag_item.id_bag == bag.id).select()
    # delete the bag if there are no items
    if not bag_items:
        db(db.bag.id == bag.id).delete()
        auto_bag_selection()
        redirection()
    check_bag_items_integrity(bag_items, True) # allow out of stock items

    # clients create orders
    if auth.has_membership('Clients'):
        bag.is_on_hold = True
        bag.update_record()
        redirect(URL('sale_order', 'create', args=bag.id))

    url = URL('ticket', args=bag.id)
    if auth.has_membership('Sales checkout'):
        url = URL('sale', 'create', args=bag.id)
    bag.status = BAG_COMPLETE
    bag.completed = True
    bag.update_record()
    auto_bag_selection()
    redirect(url)

    # SALES_WORKFLOW.next(request.controller, request.function, args, vars)


@auth.requires_membership('Stock transfers')
def stock_transfer():
    """ """

    bag = is_modifiable_bag(session.current_bag)

    # check if all the bag items are consistent
    bag_items = db(db.bag_item.id_bag == bag.id).select()
    # delete the bag if there are no items
    if not bag_items:
        db(db.bag.id == bag.id).delete()
        auto_bag_selection()
        redirection()

    check_bag_items_integrity(bag_items)

    # create stock transfer record
    new_stock_transfer_id = db.stock_transfer.insert(id_store_from=bag.id_store.id, id_bag=bag.id)
    bag.completed = True
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
        bag = db.bag.insert(id_store=session.store, completed=False)
        session.current_bag = bag.id

        return dict(bag=bag)
    except:
        import traceback
        traceback.print_exc()

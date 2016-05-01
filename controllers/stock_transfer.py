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

from item_utils import remove_stocks


@auth.requires_membership('Stock transfers')
def ticket():
    redirect( URL( 'ticket', 'get', vars=dict(id_stock_transfer=request.args(0)) ) )


@auth.requires_membership('Stock transfers')
def receive():
    """ args: [id_stock_transfer] """

    stock_transfer = db.stock_transfer(request.args(0))
    if not stock_transfer:
        raise HTTP(404)
    if stock_transfer.is_done:
        raise HTTP(405)

    bag_items = db(db.bag_item.id_bag == stock_transfer.id_bag.id).select()
    for bag_item in bag_items:
        avg_buy_price = DQ(bag_item.total_buy_price) / DQ(bag_item.quantity)

        if bag_item.id_item.is_bundle:
            bundle_items = db(db.bundle_item.id_bundle == bag_item.id_item).select()
            avg_buy_price = DQ(bag_item.total_buy_price) / DQ(bag_item.quantity) / DQ(len(bundle_items)) if bag_item.total_buy_price else 0
            for bundle_item in bundle_items:
                reintegrate_stock(bundle_item.id_item, bundle_item.quantity * bag_item.quantity, avg_buy_price, 'id_stock_transfer', stock_transfer.id)
        else:
            reintegrate_stock(bag_item.id_item, bag_item.quantity, avg_buy_price, 'id_stock_transfer', stock_transfer.id)
    stock_transfer.is_done = True
    stock_transfer.id_store_to = session.store
    stock_transfer.update_record()

    session.info = T('Products added to stock')
    redirect(URL('default', 'index'))

    return locals()


@auth.requires_membership('Stock transfers')
def scan_for_receive():
    return dict()


@auth.requires_membership('Stock transfers')
def index():
    data = SUPERT(db.stock_transfer, fields=[
        'id_store_from.name', 'id_store_to.name', 'is_done'
        ], options_func=lambda row: [OPTION_BTN('receipt', URL('ticket', args=row.id), title=T('view ticket'))]
        , selectable=False, searchable=False
    )

    return locals()

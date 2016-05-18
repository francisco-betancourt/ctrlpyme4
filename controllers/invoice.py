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
# Author Francisco Betancourt <francisco@betanetweb.com>


def items_consolidate(items):
    consolidated={}
    for item in items:
        #Check if it is already in dictionary
        id_item=item.bag_item.id_item
        sale_price=item.bag_item.sale_price
        qty=item.bag_item.quantity
        if consolidated.get((id_item,sale_price)):
            consolidated[(id_item,sale_price)].append(item)
        else:
            consolidated[(id_item,sale_price)]=[item]
    return consolidated

@auth.requires_membership('Sales invoices')
def create():
    """vars: [ sales ]"""
    sales_ids=map(int,request.vars.sales.split(','))
    if not sales_ids:
        raise HTTP(404)
    items=db((db.sale.id.belongs(sales_ids))&
             (db.sale.id_bag==db.bag_item.id_bag)).select()
    #Check if products are the same and have same price
    items_con=items_consolidate(items)
    return dict(items=items,items_con=items_con)
    
    

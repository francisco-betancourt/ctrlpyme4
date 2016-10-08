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
from bag_utils import get_valid_bag
from bag_utils import refresh_bag_data
from item_utils import remove_stocks


@auth.requires_membership('Product loss')
def create():
    """
        args: [id_bag]
    """

    bag = get_valid_bag(request.args(0))
    if not bag:
        session.info = T('Bag not found')
        redirection()
    bag_only_items_list = True
    include_bag = False

    bag_items = db(db.bag_item.id_bag == bag.id).select()
    bag_items_count = len(bag_items)
    for bag_item in bag_items:
        qty = item_stock_qty(bag_item.id_item, bag.id_store)
        bag_item.quantity = min(bag_item.quantity, qty)
        if not bag_item.quantity or not bag_item.id_item.has_inventory:
            bag_item.delete_record()
            bag_items_count -= 1
        else:
            bag_item.update_record()
    refresh_bag_data(bag.id)

    if not bag_items_count:
        session.info = T('Please add items to the product loss')
        redirection()

    form = SQLFORM(db.product_loss, buttons=[INPUT(_type='submit', _value=T('Commit'), _class="btn btn-primary"), A(T('Cancel'), _class='btn btn-default', _href=URL('default', 'index')) ], _id="product_loss_form", formstyle='bootstrap3_inline')
    form.vars.id_bag = bag.id
    form.vars.id_store = bag.id_store.id

    if form.process().accepted:
        bag.status = BAG_COMPLETE
        bag.update_record()
        remove_stocks(bag_items)
        session.info = T('Product loss commited')
        redirection()
    elif form.errors:
        session.info = T('Form has errors')

    return locals()


def bag_supert(id_bag):
    import supert
    Supert = supert.Supert()

    query = (db.bag_item.id_bag == id_bag)
    return Supert.SUPERT(
        query,
        fields=[
            'product_name',
            {
                'fields':['quantity'],
                'custom_format': lambda r, f : DQ(r.quantity, True, True),
                'label_as': T('Quantity')
            }
        ],
        options_enabled=False, searchable=False
    )


@auth.requires_membership('Product loss')
def get():
    """
        args [product_loss_id]
    """
    product_loss = db.product_loss(request.args(0))
    if not product_loss:
        session.info = T('Product loss') + ' ' + T('not found')
        redirection()

    data = bag_supert(product_loss.id_bag.id)

    return locals()


@auth.requires_membership('Product loss')
def create_reason():
    form = SQLFORM(db.product_loss_reason)
    if form.process().accepted:
        response.flash = T('form accepted')
        redirect(URL('index'))
    elif form.errors:
        response.flash = T('form has errors')
    return dict(form=form)

@auth.requires_membership('Product loss')
def update_reason():
    reason = db.product_loss_reason(request.args(0))
    form = SQLFORM(db.product_loss_reason, reason)
    if form.process().accepted:
        response.flash = T('form accepted')
        redirect(URL('index'))
    elif form.errors:
        response.flash = T('form has errors')
    return dict(form=form)

# @auth.requires_membership('Product loss')
# def hide_reason():
#     pass
#
# @auth.requires_membership('Product loss')
# def unhide_reason():
#     pass


@auth.requires_membership('Product loss')
def index():
    import supert
    Supert = supert.Supert()

    def options(row):
        return supert.OPTION_BTN(
            'info', URL('get', args=row.id), title=T('details')
        )

    data = Supert.SUPERT(
        (db.product_loss.id_store == session.store),
        fields=[
            'id_store.name', 'created_on',
            {
                'fields': ['created_by.first_name', 'created_by.last_name'],
                'label_as': T('Created by')
            }, 'notes', 'id_reason.name'
        ],
        options_func=options, global_options=[]
    )


    def reason_options(row):
        options = supert.OPTION_BTN(
            'edit', URL('update_reason', args=row.id), title=T('update')
        )
        # if row.is_active:
        #     options += OPTION_BTN(
        #         'visibility_off', URL('hide_reason', args=row.id), title=T('hide')
        #     ),
        # else:
        #     options += OPTION_BTN(
        #         'visibility', URL('unhide_reason', args=row.id), title=T('unhide')
        #     ),

        return options

    reasons = Supert.SUPERT(
        (db.product_loss_reason.is_active == True),
        fields=[ 'name' ], options_func=reason_options
    )

    return locals()

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

# sales API


from gluon import current

import common_utils
from common_utils import D, DQ

from constants import BAG_COMPLETE
from cp_errors import CP_PaymentError

import item_utils


# constants
SALE_DEFERED = 'defered'
SALE_DELIVERED = 'delivered'
SALE_CREATED = 'created'
SALE_PAID = 'paid'


def new(bag, id_store, now, user):
    """ """
    db = current.db

    bag_items = db(db.bag_item.id_bag == bag.id).iterselect()
    #TODO check discounts coherence
    for bag_item in bag_items:
        discounts = item_utils.item_discounts(bag_item.id_item)
        original_price = bag_item.sale_price + bag_item.discount

        # this is the discount coherence check, for now it does nothing
        discounted_price = item_utils.apply_discount(discounts, original_price)
        if bag_item.sale_price == discounted_price:
            pass

    # bag was created by a client
    id_store = bag.id_store.id if bag.id_store else id_store
    id_client = bag.created_by.id if bag.created_by.is_client else None

    new_sale_id = db.sale.insert(
        id_bag=bag.id, subtotal=bag.subtotal, taxes=bag.taxes,
        total=bag.total, quantity=bag.quantity,
        reward_points=bag.reward_points, id_store=id_store, id_client=id_client,
        created_by=user.id, created_on=now, modified_on=now
    )

    bag.created_by = user.id
    bag.id_store = id_store
    bag.is_sold = True
    bag.status = BAG_COMPLETE
    bag.update_record()

    if bag.is_paid:
        stripe_payment_opt = db(
            db.payment_opt.name == 'stripe'
        ).select().first()
        db.payment.insert(
            id_payment_opt=stripe_payment_opt.id, id_sale=new_sale,
            amount=bag.total, stripe_charge_id=bag.stripe_charge_id,
            is_updatable=False
        )

    return new_sale_id



def verify_payments(payments, sale, check_total=True):
    """ """

    err = ""

    if not payments:
        err = T('There are no payments')
    # verify payments consistency
    payments_total = 0
    bad_payments = False
    for payment in payments:
        if payment.id_payment_opt.credit_days > 0 and not sale.id_client:
            err = T('Credit payments only allowed for registered clients, please select a client or remove the payment')

        payments_total += payment.amount - payment.change_amount
        if payment.amount <= 0:
            payment.delete_record()
        elif not common_utils.valid_account(payment):
            bad_payments = True
    if payments_total < sale.total and check_total:
        err = T('Payments amount is lower than the total')
    if bad_payments:
        err = T('Some payments requires account')

    if err:
        raise CP_PaymentError(err)


def create_sale_event(sale, event_name, event_date=None):
    request = current.request
    db = current.db

    event_date = request.now if not event_date else event_date

    sale.last_log_event = event_name
    sale.last_log_event_date = event_date
    return db.sale_log.insert(
        id_sale=sale.id, sale_event=event_name, event_date=event_date
    )


def complete(sale):
    """ """

    db = current.db

    payments = db(db.payment.id_sale == sale.id).select()
    verify_payments(payments, sale)

    # verify items stock
    bag_items = db(db.bag_item.id_bag == sale.id_bag.id).iterselect()
    requires_serials = False  #TODO implement serial numbers
    for bag_item in bag_items:
        # since created bags does not remove stock, there could be more bag_items than stock items, so we need to check if theres enough stock to satisfy this sale, and if there is not, then we need to notify the seller or user
        stock_qty = item_utils.item_stock_qty(
            bag_item.id_item, sale.id_store.id, bag_item.id_bag.id
        )
        # this has to be done since using item_stock_qty with a bag specified will
        # consider bagged items as missing, thus we have to add them back,
        # item_stock_qty must be called with a bag because that way it will
        # count bundled items with the specified item
        stock_qty += bag_item.quantity
        # Cannot deliver a sale with out of stock items
        if stock_qty < bag_item.quantity:
            raise CP_OutOfStockError(
                T("You can't create a counter sale with out of stock items")
            )
        requires_serials |= bag_item.id_item.has_serial_number or False

    # for every payment with a payment option with credit days, set payment to not settled
    for payment in payments:
        if payment.id_payment_opt.credit_days > 0:
            payment.epd = date(request.now.year, request.now.month, request.now.day) + timedelta(days=payment.id_payment_opt.credit_days)
            payment.is_settled = False
            payment.update_record();

    store = db(db.store.id == sale.id_store.id).select(for_update=True).first()
    sale.consecutive = store.consecutive
    sale.is_done = True
    create_sale_event(sale, SALE_PAID)
    sale.update_record()
    store.consecutive += 1;
    store.update_record()

    # if defered sale, remove sale order
    db(db.sale_order.id_sale == sale.id).delete()

    # add reward points to the client's wallet, we assume that the user has a wallet
    if sale.id_client and sale.id_client.id_wallet:
        wallet = db.wallet(sale.id_client.id_wallet.id)
        wallet.balance += sale.reward_points
        wallet.update_record()


def add_payment(sale, payment_opt):
    """ Add a payment to the specified sale """

    db = current.db
    T = current.T

    add_new_payment = False

    # allow multiple payments for the same payment option
    if payment_opt.requires_account or common_utils.is_wallet(payment_opt) or sale.is_defered:

        add_new_payment = True
    else:
        # get payments with the same payment option
        payment = db((db.payment.id_sale == sale.id)
            & (db.payment.id_payment_opt == payment_opt.id)
            & (db.payment.is_updatable == True)
        ).select().first()
        if not payment:
            add_new_payment = True

    if add_new_payment:
        new_payment_id = db.payment.insert(id_payment_opt=payment_opt.id, id_sale=sale.id)
        return new_payment_id
    else:
        raise CP_PaymentError(
            T("You already have a payment with that payment option.")
        )



def get_payments_data(id_sale):
    db = current.db


    payments = db(db.payment.id_sale == id_sale).select()

    total = 0
    change = 0
    for payment in payments:
        total += (payment.amount or 0)
        change += (payment.change_amount or 0)

    return total, change, payments



def modify_payment(sale, payment, payment_data, delete=False):
    """
        payment_data: {
            'amount',
            'wallet_code',
            'account'
        }

    """

    db = current.db
    T = current.T


    new_amount = payment_data.get('amount')

    # is wallet payment
    if payment.wallet_code:
        new_amount = payment.amount

    # delete payment
    if delete:
        new_amount = 0

    # since calling this function, could cause modification to other payments, we have to store the modified payments, so the client can render the changes
    extra_updated_payments = []
    total, change, payments = get_payments_data(sale.id)
    new_total = total - change - (payment.amount - payment.change_amount) + new_amount
    if new_total > sale.total:
        # when the payment does not allow change, cut the amount to the exact remaining
        if not payment.id_payment_opt.allow_change:
            new_amount -= new_total - sale.total
    else:
        remaining = sale.total - new_total
        # when the payment modification makes the new total lower than the sale total, we have to find all the payments with change > 0 (if any) and recalculate their amount and their change
        for other_payment in payments:
            if not other_payment.id_payment_opt.allow_change or other_payment.id == payment.id:
                continue
            if remaining == 0:
                break
            if other_payment.change_amount > 0:
                new_remaining = min(remaining, other_payment.change_amount)
                new_change = other_payment.change_amount - new_remaining
                remaining -= new_remaining
                other_payment.change_amount = new_change
                other_payment.update_record()
                extra_updated_payments.append(other_payment)

    change = max(0, new_total - sale.total)
    account = payment_data.get('account')
    wallet_code = payment_data.get('wallet_code')
    # fix payment info
    if not payment.id_payment_opt.allow_change:
        change = 0
    if not payment.id_payment_opt.requires_account:
         account = None
    if not common_utils.is_wallet(payment.id_payment_opt):
         wallet_code = None
    else:
        if payment.wallet_code:
            # return wallet funds, if the wallet payment is removed or the wallet code is changed
            if delete or wallet_code != payment.wallet_code:
                wallet = db(db.wallet.wallet_code == payment.wallet_code).select().first()
                if wallet:
                    wallet.balance += payment.amount
                    wallet.update_record()
        else:
            new_amount = 0

        # only accept the first wallet code specified
        if wallet_code != payment.wallet_code:
            wallet = db(db.wallet.wallet_code == wallet_code).select().first()
            if wallet:
                new_amount = min(wallet.balance, sale.total - new_total)
                wallet.balance -= new_amount
                wallet.update_record()
            # if the code is invalid, remove its specified value
            else:
                wallet_code = None
                new_amount = 0

    payment.amount = new_amount
    payment.change_amount = change
    payment.account = account
    payment.wallet_code = wallet_code
    payment.update_record()
    if not delete:
        extra_updated_payments.append(payment)
    elif payment.is_updatable:
        payment.delete_record()

    # get the total payments data
    payments_data = get_payments_data(sale.id)
    # amount - change_amount
    payments_total = payments_data[0] - payments_data[1]

    data = dict(
        payments_total=payments_total,
        updated_payments=extra_updated_payments
    )

    return data



def deliver(sale):
    """ Sets the sale as delivered, removing its items from the stock """

    from item_utils import remove_stocks

    db = current.db

    bag_items = db(db.bag_item.id_bag == sale.id_bag.id).iterselect()
    remove_stocks(bag_items)
    create_sale_event(sale, SALE_DELIVERED)
    sale.update_record()


def refund(sale, return_items=[]):
    """
        Given a sale, performs a partial return if return items are specified or
        a full return otherwise, creating a credit note in the process
    """

    full_refund = False

    if not return_item:
        full_refund = True
        return_items = db(
            db.bag_item.id_sale == sale.id
        ).iterselect(db.bag_item.id, db.bag_item.quantity)

    def return_items_iter():
        for return_item in return_items:
            if not full_refund:
                bag_item = return_item[0]
                qty = return_item[1]
            else:
                bag_item = db.bag_item(return_item.id)
                qty = return_item.quantity
            yield bag_item_id, qty

    id_new_credit_note = db.credit_note.insert(
        id_sale=sale.id, is_usable=True
    )

    subtotal = 0
    total = 0
    returned_item_qty = 0
    for bag_item, qty in return_items_iter():
        if bag_item.id_bag != sale.id_bag.id:
            continue
        max_return_qty = max(min(bag_items_data[id_bag_item].quantity, DQ(quantity)), 0) if bag_items_data[id_bag_item] else 0
        if max_return_qty:
            # add the credit note item

            # credit_note_item = db.credit_note_item.insert(
            #
            # )
            credit_note_items[id_bag_item] = max_return_qty
            subtotal += bag_items_data[id_bag_item].sale_price * max_return_qty
            total += subtotal + bag_items_data[id_bag_item].sale_taxes * max_return_qty
            returned_items_qty += max_return_qty
        pass


    return credit_note




    r_items = form.vars.returned_items.split(',')
    # stores the returned item quantity, accesed via bag item id
    credit_note_items = {}
    # calculate subtotal and total, also validate the specified return items
    subtotal, total = 0, 0
    returned_items_qty = 0 # stores the total number of returned items
    # consider returnable items only if the sale has been delivered
    if is_delivered:
        for r_item in r_items:
            id_bag_item, quantity = r_item.split(':')[0:2]
            # check if the item was sold in the specified sale
            max_return_qty = max(min(bag_items_data[id_bag_item].quantity, DQ(quantity)), 0) if bag_items_data[id_bag_item] else 0
            if max_return_qty:
                credit_note_items[id_bag_item] = max_return_qty
                subtotal += bag_items_data[id_bag_item].sale_price * max_return_qty
                total += subtotal + bag_items_data[id_bag_item].sale_taxes * max_return_qty
                returned_items_qty += max_return_qty
    # set total to payments total
    elif sale.is_defered:
        total = payments_total
        subtotal = total

    # create the credit note
    if returned_items_qty or sale.is_defered:
        # select wallet
        create_new_wallet = False
        wallet = None
        if sale.id_client:
            client = db.auth_user(sale.id_client)
            wallet = client.id_wallet
        # add funds to the specified wallet
        elif form.vars.wallet_code:
            wallet = db(db.wallet.wallet_code == form.vars.wallet_code).select().first()
            # if the specified wallet was not found, create a new one
            create_new_wallet = not wallet
        else:
            create_new_wallet = True
        if create_new_wallet:
            wallet = db.wallet(new_wallet())
        # add wallet funds
        wallet.balance += total
        wallet.update_record()
        session.info = INFO(
            T('Sale returned, your wallet code is: ') + wallet.wallet_code,
            T('Print'), URL('wallet', 'print_wallet', args=wallet.id), 'blank'
        )
        id_new_credit_note = db.credit_note.insert(id_sale=sale.id, subtotal=subtotal, total=total, is_usable=True, code=wallet.wallet_code)

        # remove sale orders if any
        if sale.is_defered:
            db(db.sale_order.id_sale == sale.id).delete()

        # add the credit note items and reintegrate stocks.
        if is_delivered:
            for bag_item_id in credit_note_items.iterkeys():
                returned_qty = credit_note_items[bag_item_id]
                # add credit note item
                db.credit_note_item.insert(id_bag_item=bag_item_id, quantity=returned_qty, id_credit_note=id_new_credit_note)
                # return items to stock
                bag_item = bag_items_data[bag_item_id]
                id_item = bag_item.id_item.id
                avg_buy_price = DQ(bag_item.total_buy_price) / DQ(bag_item.quantity)

                # stock reintegration
                if bag_item.id_item.is_bundle:
                    bundle_items = db(db.bundle_item.id_bundle == bag_item.id_item).select()
                    avg_buy_price = DQ(bag_item.total_buy_price) / DQ(returned_items) / DQ(len(bundle_items)) if bag_item.total_buy_price else 0
                    for bundle_item in bundle_items:
                        reintegrate_stock(bundle_item.id_item, bundle_item.quantity * returned_qty, avg_buy_price, 'id_credit_note', id_new_credit_note)
                else:
                    reintegrate_stock(bag_item.id_item, returned_qty, avg_buy_price, 'id_credit_note', id_new_credit_note)
    pass


def commit():
    pass


def cancel():
    pass

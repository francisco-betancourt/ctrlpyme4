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


import json
from uuid import uuid4


def ticket():
    redirect( URL( 'ticket', 'get', vars=dict(id_sale=request.args(0)) ) )


def get_payments_data(id_sale):
    payments = db(db.payment.id_sale == id_sale).select()

    total = 0
    change = 0
    for payment in payments:
        total += (payment.amount or 0)
        change += (payment.change_amount or 0)

    return total, change, payments


def valid_sale(sale):
    if not sale.created_by.id == auth.user.id:
        raise HTTP(401)
    if not sale:
        raise HTTP(404)
    if sale.is_done:
        session.info = {
            'text': 'Sale has been paid',
            'btn': {'text': T('View ticket'), 'target': '_blank' , 'href': URL('sale', 'ticket', args=sale.id)}
        }
        redirect(URL('default', 'index'))
    return True



@auth.requires_membership('Sales checkout')
def add_payment():
    """ Adds a payment related to a bag, with the specified payment option
        args: [id_sale, id_payment_opt]
    """

    sale = db.sale(request.args(0))
    valid_sale(sale)

    # check if the payments total is lower than the total
    s = db.payment.amount.sum()
    payments_total = db(db.payment.id_sale == sale.id).select(s).first()[s]
    if not payments_total < db.sale(sale.id).total:
        raise HTTP(405)

    payment_opt = db.payment_opt(request.args(1))
    if not payment_opt:
        raise HTTP(404)

    # only accept credit payments for registered clients
    if payment_opt.credit_days > 0 and not sale.id_client:
        raise HTTP(405)

    add_new_payment = False

    # allow multiple payments for the same payment option
    if payment_opt.requires_account or is_wallet(payment_opt) or sale.is_defered:
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
        new_payment = db.payment(db.payment.insert(id_payment_opt=payment_opt.id, id_sale=sale.id))
    else:
        raise HTTP(405)

    return dict(payment_opt=payment_opt, payment=new_payment)


@auth.requires_membership('Sales checkout')
def update_payment():
    """
        args: [id_sale, id_payment]
        vars: [amount, account, wallet_code, delete]
    """

    sale = db.sale(request.args(0))
    valid_sale(sale)

    payment = db((db.payment.id == request.args(1))
               & (db.payment.id_sale == sale.id)).select().first()
    if not payment:
        raise HTTP(404)
    if not payment.is_updatable:
        raise HTTP(405)

    # Accept updates for 7 minutes
    if (request.now - payment.created_on).seconds / 60.0 / 7.0 > 1:
        if sale.is_defered:
            payment.is_updatable = False
            payment.update_record()
        raise HTTP(405)

    try:
        new_amount = D(request.vars.amount or payment.amount)
    except:
        raise HTTP(417)

    if payment.wallet_code:
        new_amount = payment.amount
        wallet_code = payment.wallet_code

    if request.vars.delete:
        new_amount = 0

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
                # other_payment.amount += new_remaining
                other_payment.update_record()
                other_payment.amount = str(DQ(other_payment.amount, True))
                other_payment.change_amount = str(DQ(other_payment.change_amount, True))
                extra_updated_payments.append(other_payment)

    change = max(0, new_total - sale.total)
    account = request.vars.account
    wallet_code = request.vars.wallet_code
    if not payment.id_payment_opt.allow_change:
        change = 0
    if not payment.id_payment_opt.requires_account:
         account = None
    if not is_wallet(payment.id_payment_opt):
         wallet_code = None
    else:
        if payment.wallet_code:
            # return wallet funds
            if request.vars.delete:
                wallet = db(db.wallet.wallet_code == payment.wallet_code).select().first()
                if wallet:
                    wallet.balance += payment.amount
                    wallet.update_record()

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

    payment.amount = str(DQ(payment.amount, True))
    payment.change_amount = str(DQ(payment.change_amount, True))
    if not request.vars.delete:
        extra_updated_payments.append(payment)
    elif payment.is_updatable:
        payment.delete_record()

    return dict(updated=extra_updated_payments)



@auth.requires_membership('Sales checkout')
def cancel():
    """ args: [id_sale] """

    sale = db.sale(request.args(0))
    valid_sale(sale)
    # cannot cancel a defered sale, without credit note and all that stuff
    if sale.is_defered:
        raise HTTP(405)

    # return wallet payments
    wallet_opt = get_wallet_payment_opt()
    payments = db((db.payment.id_payment_opt == wallet_opt.id) & (db.payment.id_sale == sale.id)).select()
    for payment in payments:
        wallet = db(db.wallet.wallet_code == payment.wallet_code).select().first()
        wallet.balance += payment.amount
        wallet.update_record()

    # delete the bag and all its bag items
    db(db.bag_item.id_bag == sale.id_bag.id).delete()
    db(db.bag.id == sale.id_bag.id).delete()
    db(db.payment.id_sale == sale.id).delete()
    db(db.sale_order.id_bag == sale.id_bag.id).delete()
    sale.delete_record()

    redirection()


@auth.requires_membership('Sales checkout')
def update():
    """ args: [id_sale] """

    sale = db.sale(request.args(0))
    valid_sale(sale)

    clients = db(db.auth_user.is_client == True).select()

    payments = db(db.payment.id_sale == sale.id).select()
    payment_options = db(db.payment_opt.is_active == True).select()

    return locals()


@auth.requires_membership('Sales checkout')
def set_sale_client():
    """ args: [id_sale, id_client] """

    sale = db.sale(request.args(0))
    valid_sale(sale)
    if sale.is_defered:
        raise HTTP(405)
    client = db((db.auth_user.is_client == True)
                & (db.auth_user.registration_key == '')
                & (db.auth_user.id == request.args(1))
                ).select().first()
    wallet = None
    #TODO remove credit payments if the user is None
    if not client:
        sale.id_client = None
    else:
        sale.id_client = client.id
        if client.id_wallet:
            wallet = client.id_wallet
            wallet = db.wallet(wallet)
            wallet.balance = str(DQ(wallet.balance, True))
    sale.update_record()

    return dict(wallet=wallet)


@auth.requires_membership('Sales checkout')
def create():
    """ args: [ id_bag ] """

    bag = db.bag(request.args(0))
    if not bag:
        raise HTTP(404)
    # theres a sale asociated with the specified bag
    if db(db.sale.id_bag == bag.id).select().first():
        session.info = T('Bag already sold')
        redirect(URL('default', 'index'))

    bag_items = db(db.bag_item.id_bag == bag.id).select()
    #TODO check discounts coherence
    for bag_item in bag_items:
        discounts = item_discounts(bag_item.id_item)
        original_price = bag_item.sale_price + bag_item.discount
        if bag_item.sale_price == apply_discount(discounts, original_price):
            print 'ok'

    new_sale = db.sale.insert(id_bag=bag.id, subtotal=bag.subtotal, taxes=bag.taxes, total=bag.total, quantity=bag.quantity, reward_points=bag.reward_points, id_store=bag.id_store.id)

    redirect(URL('update', args=new_sale))



def verify_payments(payments, sale, check_total=True):
    if not payments:
        session.info = T('There are no payments')
        redirect(URL('update', args=sale.id))
    # verify payments consistency
    payments_total = 0
    bad_payments = False
    for payment in payments:
        if payment.id_payment_opt.credit_days > 0 and not sale.id_client:
            session.info = T('Credit payments only allowed for registered clients, please select a client or remove the payment')
            redirect(URL('update', args=sale.id))

        payments_total += payment.amount - payment.change_amount
        if not valid_account(payment):
            bad_payments = True
        if payment.amount <= 0:
            payment.delete_record()
    if payments_total < sale.total and check_total:
        session.info = T('Payments amount is lower than the total')
        redirect(URL('update', args=sale.id))
    if bad_payments:
        session.info = T('Some payments requires account')
        redirect(URL('update', args=sale.id))


@auth.requires_membership('Sales checkout')
def complete():
    """
        args: [id_sale]
    """
    sale = db.sale(request.args(0))
    valid_sale(sale)

    payments = db(db.payment.id_sale == sale.id).select()
    verify_payments(payments, sale)

    # verify items stock
    bag_items = db(db.bag_item.id_bag == sale.id_bag.id).select()
    requires_serials = False  #TODO implement serial numbers
    for bag_item in bag_items:
        # since created bags does not remove stock, there could be more bag_items than stock items, so we need to check if theres enough stock to satisfy this sale, and if there is not, then we need to notify the seller or user
        stocks, stock_qty = item_stock(bag_item.id_item, session.store).itervalues()
        # Cannot deliver a sale with out of stock items
        if stock_qty <= bag_item.quantity:
            session.info = T("You can't create a counter sale with out of stock items")
            redirect(URL('update', args=sale.id))
        requires_serials |= bag_item.id_item.has_serial_number or False

    # for every payment with a payment option with credit days, set payment to not settled
    for payment in payments:
        if payment.id_payment_opt.credit_days > 0:
            payment.is_settled = False
            payment.update_record();

    store = db(db.store.id == session.store).select(for_update=True).first()
    sale.consecutive = store.consecutive
    sale.is_done = True
    store.consecutive += 1;
    store.update_record()
    sale.update_record()
    db.sale_log.insert(id_sale=sale.id, sale_event="paid")

    # if defered sale, remove sale order
    db(db.sale_order.id_sale == sale.id).delete()

    # add reward points to the client's wallet
    if sale.id_client:
        wallet = db.wallet(sale.id_client.id_wallet.id)
        wallet.balance += sale.reward_points
        wallet.update_record()

    #TODO check company workflow
    if not auth.has_membership('Sales delivery'):
        redirect(URL('scan_ticket'))
    else:
        bag_items = db(db.bag_item.id_bag == sale.id_bag.id).select()
        remove_stocks(bag_items)
        db.sale_log.insert(id_sale=sale.id, sale_event="delivered")
        redirect(URL('ticket', args=sale.id, vars={'_print': True}))


@auth.requires_membership('Sales checkout')
def defer():
    """ args: [id_sale] """
    sale = db.sale(request.args(0))
    valid_sale(sale)

    payments = db(db.payment.id_sale == sale.id).select()
    verify_payments(payments, sale, False)
    payments = db(db.payment.id_sale == sale.id).select()
    # Since this sale will be edited later we have to make sure that current payments will not be modified, so we set them as non updatable
    for payment in payments:
        payment.is_updatable = False;
        payment.update_record()

    # if defered function is called on a defered sale, we skip the following steps
    if not sale.is_defered:
        sale.is_defered = True
        sale.update_record()
        db.sale_log.insert(id_sale=sale.id, sale_event="defered")

        # create sale order based on the
        db.sale_order.insert(id_store=session.store, id_bag=sale.id_bag.id, id_sale=sale.id, is_for_defered_sale=True)

    redirect(URL('ticket', args=sale.id, vars={'_print': True}))


@auth.requires_membership('Sales delivery')
def deliver():
    """ args: [sale_id] """

    sale = db.sale(request.args(0))
    if not sale:
        raise HTTP(404)
    # find all the sold items whose purchase had serial numbers
    bag_items = db(db.bag_item.id_bag == sale.id_bag.id).select()
    resume = DIV()
    for bag_item in bag_items:
        resume.append(bag_item.product_name + str(DQ(bag_item.quantity, True)) + ' x $' + str(DQ(bag_item.sale_price, True)))

    form = SQLFORM.factory(
        submit_button=T("Deliver")
    )
    form[0].insert(0, sqlform_field("", "", resume))

    if form.process().accepted:
        db.sale_log.insert(id_sale=sale.id, sale_event="Delivered")

    return locals()


@auth.requires(auth.has_membership('Sales returns')
            or auth.has_membership('Sales checkout')
            )
def get():
    """
        args: [sale_id]
    """

    sale = db.sale(request.args(0))
    return dict(sale=sale)


@auth.requires(auth.has_membership('Sales returns')
            or auth.has_membership('Sales checkout')
            or auth.has_membership('Sales invoices')
            )
def get_by_barcode():
    """
        args: [barcode]
    """

    try:
        barcode = int(request.args(0))

        sale = db.sale(barcode)
        if not sale:
            raise HTTP(404)
        if sale.is_invoiced:
            raise HTTP(404)
        return dict(sale=sale)
    except:
        raise HTTP(404)


@auth.requires_membership('Sales checkout')
def scan_ticket():
    return dict()


@auth.requires_membership('Sales invoices')
def scan_for_invoice():
    return dict()


@auth.requires_membership('Sales returns')
def scan_for_refund():
    return dict()


@auth.requires_membership('Sales returns')
def refund():
    """ Performs the logic to refund a sale

        args: [sale_id]
    """

    sale = db.sale(request.args(0))
    if not sale:
        raise HTTP(404)

    # check if the sale has been delivered
    is_delivered = db((db.sale_log.id_sale == sale.id) & (db.sale_log.sale_event == "delivered")).select().first()
    if not is_delivered and not sale.is_defered:
        session.info = T('The sale has not been delivered!')
        redirect(URL('scan_for_refund'))

    payments_total = 0
    payments = db(db.payment.id_sale == sale.id).select()
    for payment in payments:
        payments_total += payment.amount - payment.change_amount

    invalid = False
    bag_items_data = {}
    bag_items = []
    returnable_items_qty = 0

    if is_delivered:
        # obtain all returnable items from the specified sale
        query_result = db((db.bag_item.id_item == db.item.id)
                        & (db.bag_item.id_bag == sale.id_bag.id)
                        & (db.item.is_returnable == True)
                         ).select(db.bag_item.ALL)
        for row in query_result:
            bag_items.append(row)
            bag_items_data[str(row.id)] = row
            returnable_items_qty += row.quantity

        # check if there's still unreturned items
        returned_items = db(
               (db.credit_note.id_sale == db.sale.id)
             & (db.credit_note_item.id_credit_note == db.credit_note.id)
             & (db.sale.id == sale.id)
                ).select(db.credit_note_item.ALL)
        for row in returned_items:
            bag_items_data[str(row.id_bag_item)].quantity -= row.quantity
            returnable_items_qty -= row.quantity
        invalid = returnable_items_qty <= 0
    # since pure defered sales does not remove stocks, we can only refund all payments once, so we have to make sure that there are no credit notes associated with the specified sale
    elif sale.is_defered:
        credit_note = db(db.credit_note.id_sale == sale.id).select().first()
        invalid = not not credit_note

    form = SQLFORM.factory(
        Field('wallet_code', label=T('Wallet Code'))
        , Field('returned_items')
        , submit_button=T("Refund")
    )

    if form.process().accepted:
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
                            reintegrate_stock(bundle_item.id_item, bundle_item.quantity * returned_qty, avg_buy_price, id_new_credit_note)
                    else:
                        reintegrate_stock(bag_item.id_item, returned_qty, avg_buy_price, id_new_credit_note)
        redirect(URL('credit_note', 'get', args=id_new_credit_note))
    return locals()


def sale_row(row, fields):
    tr = TR()
    # sale status
    last_log = db(db.sale_log.id_sale == row.id).select().last()
    sale_event = last_log.sale_event if last_log else None
    tr.append(TD(T(sale_event or 'Unknown')))
    for field in fields:
        tr.append(TD(row[field]))
    return tr


def sale_extra_options(row):
    return [option_btn('', URL('ticket', args=row.id), action_name=T('ticket')),
            option_btn('', URL('invoice', 'create'), action_name=T('Invoice'))]



@auth.requires_membership("Sales invoices")
def index():
    data = common_index('sale', ['consecutive', 'subtotal', 'total'], dict(row_function=sale_row, custom_headers=['Status', 'Consecutive', 'Subtotal', 'Total'], options_function=lambda row: [], extra_options=sale_extra_options))
    return locals()

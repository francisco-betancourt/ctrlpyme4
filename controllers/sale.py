# -*- coding: utf-8 -*-
#
# Author: Daniel J. Ramirez

import json
from uuid import uuid4


def _remove_stocks(item, quantity, sale_date):
    if not item.has_inventory:
        return 0, 0
    if not quantity:
        return 0, 0
    original_qty = quantity
    stock_items, quantity = item_stock(item, session.store).itervalues()
    quantity = DQ(quantity)
    total_buy_price = 0
    wavg_days_in_shelf = 0
    for stock_item in stock_items:
        if not quantity:
            return 0, 0
        stock_qty = DQ(stock_item.stock_qty) - DQ(original_qty)
        stock_item.stock_qty = max(0, stock_qty)
        stock_item.update_record()
        quantity = abs(stock_qty)

        total_buy_price += original_qty * (stock_item.price or 0)
        days_since_purchase = (sale_date - stock_item.created_on).days
        wavg_days_in_shelf += days_since_purchase
    wavg_days_in_shelf /= original_qty

    return total_buy_price, wavg_days_in_shelf


def remove_stocks(bag_items):
    for bag_item in bag_items:
        #TODO:50 implement stock removal for bag items with serial number
        if bag_item.id_item.has_serial_number:
            pass
        else:
            bag_item_total_buy_price = 0
            # when we have a bundle, we have to remove stocks for every item in the bundle. Since bundles cannot be purchased, we have to consider its average days in shelf, as the average of its bundle items weighted average days in shelf
            if bag_item.id_item.is_bundle:
                total_wavg_days_in_shelf = 0
                bundle_items_qty = 0
                bundle_items = db(db.bundle_item.id_bundle == bag_item.id_item.id).select()
                for bundle_item in bundle_items:
                    bundle_items_qty += 1
                    total_buy_price, wavg_days_in_shelf = _remove_stocks(bundle_item.id_item, bundle_item.quantity, bag_item.created_on)
                    total_wavg_days_in_shelf += wavg_days_in_shelf
                    bag_item_total_buy_price += total_buy_price
                total_wavg_days_in_shelf /= bundle_items_qty

                bag_item.total_buy_price = bag_item_total_buy_price
                bag_item.wavg_days_in_shelf = total_wavg_days_in_shelf

                bag_item.update_record()
            else:
                total_buy_price, wavg_days_in_shelf = _remove_stocks(bag_item.id_item, bag_item.quantity, bag_item.created_on)
                bag_item.total_buy_price = total_buy_price
                bag_item.wavg_days_in_shelf = wavg_days_in_shelf

                bag_item.update_record()


def validate_sale_form(form):
    payments = db(db.payment.id_bag == form.vars.id_bag).select()
    total = 0
    for payment in payments:
        requires_account = payment.id_payment_opt.requires_account
        total += DQ(payment.amount)
        if payment.account and len(payment.account) != 4 and requires_account:
            form.errors.payments_data = T('Some payments require an account')
            return
    if total < form.vars.total:
        form.errors.payments_data = T('Payments amount is lower than the total')


@auth.requires_membership('Sales checkout')
def ticket():
    """
        args:
            id_sale
    """

    sale = db.sale(request.args(0))
    print_ticket = request.vars.print_ticket

    if not sale:
        raise HTTP(404)
    # format ticket barcode
    ticket_barcode = "%010d" % sale.id
    # get bag items data
    bag_items = db(db.bag_item.id_bag == sale.id_bag.id).select()

    ticket = create_ticket('Sale', sale.id_store, sale.created_by, bag_items, ticket_barcode, '')

    return locals()





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
    if not sale or sale.is_done:
        raise HTTP(404)
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

    add_new_payment = False

    # allow multiple payments for the same payment option
    if payment_opt.requires_account or is_wallet(payment_opt):
        add_new_payment = True
    else:
        # get payments with the same payment option
        payment = db((db.payment.id_sale == sale.id) & (db.payment.id_payment_opt == payment_opt.id)).select().first()
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
    else:
        payment.delete_record()

    return dict(updated=extra_updated_payments)



# #TODO:20 cancel sale, (dont forget) to return the wallet payments
@auth.requires_membership('Sales checkout')
def cancel():
    """
        args: [id_sale]
    """

    sale = db.sale(request.args(0))
    valid_sale(sale)

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
    """
        args: [id_sale]
    """

    sale = db.sale(request.args(0))
    valid_sale(sale)

    clients = db(db.auth_user.is_client == True).select()

    payments = db(db.payment.id_sale == sale.id).select()
    payment_options = db(db.payment_opt.is_active == True).select()


    return locals()


@auth.requires_membership('Sales checkout')
def set_sale_client():
    """
        args: [id_sale, id_client]
    """
    sale = db.sale(request.args(0))
    valid_sale(sale)
    client = db((db.auth_user.is_client == True)
                & (db.auth_user.registration_key == '')
                & (db.auth_user.id == request.args(1))
                ).select().first()
    wallet = None
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
    """
        args:
            id_bag
    """

    bag = db.bag(request.args(0))
    if not bag:
        raise HTTP(404)
    # theres a sale asociated with the specified bag
    if db(db.sale.id_bag == bag.id).select().first():
        session.info = T('Bag already sold')
        redirect(URL('default', 'index'))
    # get bag items data, calculate total, subtotal, taxes, quantity, reward points.
    bag_items = db(db.bag_item.id_bag == bag.id).select()
    total = 0
    taxes = 0
    subtotal = 0
    reward_points = 0
    quantity = 0
    requires_serials = False
    for bag_item in bag_items:
        #TODO check for existences before the sale
        # since created bags does not remove stock, there could be more bag_items than stock items, so we need to check if theres enough stock to satisfy this sale, and if there is not, then we need to notify the seller or user
        stocks, stock_qty = item_stock(bag_item.id_item, session.store).itervalues()
        # if theres no stock the user needs to modify the bag
        if stock_qty <= quantity:
            session.info = T('Some items are missing')
            redirect('default', 'index')
        subtotal += bag_item.sale_price * bag_item.quantity
        taxes += bag_item.sale_taxes * bag_item.quantity
        total += (bag_item.sale_price + bag_item.sale_taxes) * bag_item.quantity
        quantity += bag_item.quantity
        reward_points += bag_item.id_item.reward_points or 0
        requires_serials |= bag_item.id_item.has_serial_number or False
    subtotal = DQ(subtotal, True)
    taxes = DQ(taxes, True)
    total = DQ(total, True)
    quantity = DQ(quantity, True)
    reward_points = DQ(reward_points, True)

    # set bag item taxes list
    for bag_item in bag_items:
        bag_item.item_taxes = bag_item.id_item.taxes
        bag_item.update_record()

    new_sale = db.sale.insert(id_bag=bag.id, subtotal=subtotal, taxes=taxes, total=total, quantity=quantity, reward_points=reward_points, id_store=bag.id_store.id)

    redirect(URL('update', args=new_sale))


@auth.requires_membership('Sales checkout')
def complete():
    """
        args: [id_sale]
    """
    sale = db.sale(request.args(0))
    valid_sale(sale)

    payments = db(db.payment.id_sale == sale.id).select()
    if not payments:
        session.info = T('There are no payments')
        redirect(URL('update', args=sale.id))

    # verify payments consistency
    payments_total = 0
    bad_payments = False
    for payment in payments:
        payments_total += payment.amount - payment.change_amount
        if not valid_account(payment):
            bad_payments = True
        if payment.amount <= 0:
            payment.delete_record()

    if payments_total < sale.total:
        session.info = T('Payments amount is lower than the total')
        redirect(URL('update', args=sale.id))
    if bad_payments:
        session.info = T('Some payments requires account')
        redirect(URL('update', args=sale.id))

    store = db(db.store.id == session.store).select(for_update=True).first()
    sale.consecutive = store.consecutive
    sale.is_done = True
    store.consecutive += 1;
    store.update_record()
    sale.update_record()
    db.sale_log.insert(id_sale=sale.id, sale_event="paid")

    # add reward points to the client's wallet
    if sale.id_client:
        wallet = db.wallet(sale.id_client.id_wallet.id)
        wallet.balance += sale.reward_points
        wallet.update_record()

    if not auth.has_membership('Sales delivery'):
        redirect(URL('scan_ticket'))
    else:
        # if requires_serials:
        #     redirect(URL('serials', args=sale.id))
        bag_items = db(db.bag_item.id_bag == sale.id_bag.id).select()
        remove_stocks(bag_items)
        db.sale_log.insert(id_sale=sale.id, sale_event="delivered")
        redirect(URL('ticket', args=sale.id, vars={'print_ticket': True}))


@auth.requires_membership('Sales delivery')
def deliver():
    """
        args:
            sale_id
    """

    sale = db.sale(request.args(0))
    print sale
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

        args:
            sale_id
    """

    sale = db.sale(request.args(0))
    if not sale:
        raise HTTP(404)

    # check if the sale has been delivered
    if not db((db.sale_log.id_sale == sale.id) & (db.sale_log.sale_event == "delivered")).select().first():
        print "not delivered"
        response.flash = T('The sale has not been delivered!')
        redirect(URL('scan_for_refund'))


    bag = db.bag(sale.id_bag)
    bag_items_data = {}
    bag_items = []
    query_result = db((db.bag_item.id_item == db.item.id)
                    & (db.bag_item.id_bag == bag.id)
                    & (db.item.is_returnable == True)
                     ).select()
    returnable_items_qty = 0
    for row in query_result:
        bag_items.append(row.bag_item)
        bag_items_data[str(row.bag_item.id)] = row.bag_item
        returnable_items_qty += row.bag_item.quantity

    # check if there's still unreturned items
    returned_items = db(
           (db.credit_note.id_sale == db.sale.id)
         & (db.credit_note_item.id_credit_note == db.credit_note.id)
         & (db.sale.id == sale.id)
            ).select()
    for row in returned_items:
        bag_items_data[str(row.credit_note_item.id_bag_item)].quantity -= row.credit_note_item.quantity
        returnable_items_qty -= row.credit_note_item.quantity
    invalid = returnable_items_qty <= 0

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
        subtotal = 0
        total = 0
        returned_items_qty = 0 # stores the total number of returned items
        for r_item in r_items:
            id_bag_item, quantity = r_item.split(':')[0:2]
            # check if the item was sold in the specified sale
            max_return_qty = max(min(bag_items_data[id_bag_item].quantity, DQ(quantity)), 0) if bag_items_data[id_bag_item] else 0
            if max_return_qty:
                credit_note_items[id_bag_item] = max_return_qty
                subtotal += bag_items_data[id_bag_item].sale_price * max_return_qty
                total += subtotal + bag_items_data[id_bag_item].sale_taxes * max_return_qty
                returned_items_qty += max_return_qty
        # create the credit note
        if returned_items_qty:
            id_new_credit_note = db.credit_note.insert(id_sale=sale.id, subtotal=subtotal, total=total, is_usable=True)
            # create wallet and add funds to it
            wallet_code = form.vars.wallet_code
            if sale.id_client:
                client = db.auth_user(sale.id_client)
                wallet = client.id_wallet
                if not wallet:
                    client.id_wallet = new_wallet(total)
                    client.update_record()
                else:
                    wallet.balance += total
                    wallet.update_record()
                response.info = T('Sale returned, funds added to wallet for client: ') + sale.id_client.first_name
            else:
                already_added = False
                # user wallet specified
                if wallet_code:
                    wallet = db(db.wallet.wallet_code == wallet_code).select().first()
                    if wallet:
                        wallet.balance += total
                        wallet.update_record()
                        already_added = True
                    session.info = T("Sale returned, funds added to wallet") + " %s" % wallet_code
                if not already_added:
                    wallet_code = request.vars.wallet_code or uuid4()
                    id_wallet = db.wallet.insert(balance=total, wallet_code=wallet_code)
                    session.info = {
                        'text': T('Sale returned, your wallet code is: ') + wallet_code,
                        'btn': {
                            'text': T('Print'),
                            'href': URL('wallet', 'print_wallet', args=id_wallet),
                            'target': 'blank'
                        }
                    }
            # add the credit note items
            for bag_item_id in credit_note_items.iterkeys():
                returned_qty = credit_note_items[bag_item_id]
                # add credit note item
                db.credit_note_item.insert(id_bag_item=bag_item_id, quantity=returned_qty, id_credit_note=id_new_credit_note)
                # return items to stock
                bag_item = bag_items_data[bag_item_id]
                id_item = bag_item.id_item.id
                avg_buy_price = DQ(bag_item.total_buy_price) / DQ(bag_item.quantity)

                def reintegrate_stock(item, returned_qty, avg_buy_price, id_credit_note):
                    stock_item = db((db.stock_item.id_credit_note == id_credit_note) & (db.stock_item.id_item == item.id)).select().first()
                    if stock_item:
                        stock_item.purchase_qty += returned_qty
                        stock_item.stock_qty += returned_qty
                        stock_qty.update_record()
                    else:
                        db.stock_item.insert(id_credit_note=id_credit_note,
                                             id_item=item.id,
                                             purchase_qty=returned_qty,
                                             price=avg_buy_price,
                                             stock_qty=returned_qty,
                                             id_store=session.store,
                                             taxes=0
                                             )
                # stock reintegration
                if bag_item.id_item.is_bundle:
                    bundle_items = db(db.bundle_item.id_bundle == bag_item.id_item).select()
                    avg_buy_price = DQ(bag_item.total_buy_price) / DQ(returned_items) / DQ(len(bundle_items)) if bag_item.total_buy_price else 0
                    for bundle_item in bundle_items:
                        reintegrate_stock(bundle_item.id_item, bundle_item.quantity * returned_qty, avg_buy_price, id_new_credit_note)
                else:
                    reintegrate_stock(bag_item.id_item, returned_qty, avg_buy_price, id_new_credit_note)
        redirect(URL('credit_note', 'index'))
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

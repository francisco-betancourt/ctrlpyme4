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


# #TODO:20 cancel sale, (dont forget) to return the wallet payments
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


@auth.requires_membership('Sales checkout')
def scan_ticket():
    return dict()


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



def get_payments_data(id_bag):
    payments = db(db.payment.id_bag == id_bag).select()

    total = 0
    change = 0
    for payment in payments:
        total += (payment.amount or 0)
        change += (payment.change_amount or 0)

    return total, change, payments


def fix_payment_data(payment, amount, change_amount, account, wallet_code):
    """ This function will adjust the specified payment parameters in order to satisfy the global constraints, meaning it will set the correct amount, the change, the wallet code, and account, so the payment is coherent with the rest of the payments, when the payment method modification produces an inconsistent change amount, this function will reset all the payments changes, and place the total change in the modified payment """

    amount = amount or payment.amount if amount != 0 else 0
    change_amount = change_amount or payment.change_amount
    account = account or payment.account if payment.account != 'user' else 'user'
    wallet_code = wallet_code or payment.wallet_code

    bag_total = payment.id_bag.total
    payments_total, total_change, payments = get_payments_data(payment.id_bag.id)

    if not payments_total:
        payments_total = 0

    # total after the payment amount modification
    new_payments_total = payments_total - payment.amount + amount

    # when this payment allows change, then we have to recalculate all the changes from the other payments, in order to set this payment change amount
    if payment.id_payment_opt.allow_change:
        # this is the total change that will be returned on the sale
        change_amount = new_payments_total - bag_total
        change_amount = max(0, change_amount)
        # this will remove all the change amounts from payment options that can return change, the total change will be stored in the modified payment, if this payment allows change
        for other_payment in payments:
            if payment == other_payment:
                continue
            other_payment.change_amount = 0
            other_payment.update_record()
    else:
        change_amount = DQ(0, True)

    if new_payments_total > bag_total:
        amount = bag_total - payments_total + payment.amount

    # wallet payment
    if wallet_code and is_wallet(payment.id_payment_opt):
        # request wallet credit
        wallet = db(db.wallet.wallet_code == wallet_code).select().first()
        if not wallet:
            raise HTTP(404, T('Wallet not found'))
        # the wallet payment modification needs to return wallet funds
        wallet.balance = wallet.balance + payment.amount
        wallet.balance = wallet.balance - amount
        wallet.update_record()
    if (not payment.id_payment_opt.requires_account) and account != 'user':
        account = None

    return amount, change_amount, account, wallet_code


@auth.requires_membership('Sales checkout')
def modify_payment():
    """ Modifies the specified payment
        args:
            id_payment
        vars:
            payment_data
    """
    try:
        payment = db.payment(request.args(0))
        if not payment:
            raise HTTP(404)

        amount = DQ(request.vars.amount, True)
        change_amount = DQ(0, True)
        account = request.vars.account
        wallet_code = request.vars.wallet_code

        amount, change_amount, account, wallet_code = fix_payment_data(payment, amount, change_amount, account, wallet_code)

        payment.amount = amount
        payment.change_amount = change_amount
        payment.account = account
        payment.wallet_code = wallet_code
        payment.update_record()
        wallet = db(db.wallet.wallet_code == wallet_code).select().first()
        return dict(payment=payment, payments=[], wallet=wallet)
    except:
        import traceback
        traceback.print_exc()


@auth.requires_membership('Sales checkout')
def add_user_wallet_payment():
    """ Adds a payment related to a bag, with the specified payment option
        args:
            id_bag
            id_user
    """

    id_bag = request.args(0)
    bag = db.bag(id_bag)
    user = db.auth_user(request.args(1))
    wallet_payment_opt = get_wallet_payment_opt()
    if not user or not bag:
        raise HTTP(404)
    wallet = user.id_wallet

    if not wallet or wallet.balance <= 0:
        return dict()

    # check if the payments total is lower than the total
    s = db.payment.amount.sum()
    payments_total = db(db.payment.id_bag == id_bag).select(s).first()[s]

    if not payments_total < db.bag(id_bag).total:
        return dict(msg=T("You dont need to add more payments"))

    wallet_payment = db.payment.insert(id_payment_opt=wallet_payment_opt.id, id_bag=bag.id, wallet_code=wallet.wallet_code, account="user")
    wallet_payment = db.payment(wallet_payment)

    amount, change_amount, account, wallet_code = fix_payment_data(wallet_payment, wallet.balance, 0, 'user', wallet.wallet_code)

    wallet_balance = DQ(db.wallet(wallet.id).balance, True)

    wallet_payment.amount = amount
    wallet_payment.update_record()

    return dict(payment_opt=wallet_payment_opt, payment=wallet_payment, wallet_balance=wallet_balance)


@auth.requires_membership('Sales checkout')
def add_payment():
    """ Adds a payment related to a bag, with the specified payment option
        args:
            id_bag
            id_payment_opt
    """

    id_bag = request.args(0)
    bag = db.bag(id_bag)
    payment_opt = db.payment_opt(request.args(1))
    if not payment_opt or not bag:
        raise HTTP(404)

    # check if the payments total is lower than the total
    s = db.payment.amount.sum()
    payments_total = db(db.payment.id_bag == id_bag).select(s).first()[s]

    if not payments_total < db.bag(id_bag).total:
        return dict(msg=T("You dont need to add more payments"))

    new_payment = db.payment(db.payment.insert(id_payment_opt=payment_opt.id, id_bag=id_bag))

    return dict(payment_opt=payment_opt, payment=new_payment)


@auth.requires_membership('Sales checkout')
def remove_payment():
    """ removes a payment related to a bag, with the specified payment option
        args:
            id_payment
    """

    extra_params = {}

    try:
        payment = db.payment(request.args(0))
        if not payment:
            raise HTTP(404)
        id_bag = payment.id_bag.id
        if is_wallet(payment.id_payment_opt):
            # get the payment wallet
            wallet = db(db.wallet.wallet_code == payment.wallet_code).select().first()
            if wallet:
                wallet.balance += payment.amount
                wallet.update_record()
                if payment.account == 'user':
                    extra_params["wallet_balance"] = DQ(wallet.balance, True)
        payment.delete_record()

        # sice there could be other payments with some change in them, we need to recalculate the total change (if any) and add it to a payment that allows change
        total, change, payments = get_payments_data(id_bag)

        for other_payment in payments:
            other_payment.change_amount = 0
            other_payment.update_record()

        return dict(payments=payments, **extra_params)
    except:
        import traceback
        traceback.print_exc()


@auth.requires_membership('Sales checkout')
def cancel():
    """
        args: [id_bag]
    """

    bag = db.bag(request.args(0))
    if not bag:
        raise HTTP(404)
    if not bag.completed:
        raise HTTP(403)
    if not bag.created_by.is_client and bag.created_by.id != auth.user.id:
        raise HTTP(403)
    if db(db.sale.id_bag == bag.id).select().first():
        raise HTTP(403)

    # delete the bag and all its bag items
    db(db.bag_item.id_bag == bag.id).delete()
    bag.delete_record()
    db(db.sale_order.id_bag == bag.id).delete()

    redirection()


@auth.requires_membership('Sales checkout')
def create():
    """
        args:
            id_bag
    """

    bag = db.bag(request.args(0))
    if not bag:
        raise HTTP(404)
    if db(db.sale.id_bag == bag.id).select().first():
        redirect(URL('default', 'index'))
        # raise HTTP(500)
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

    # set the form data to the previously calculated values
    form = SQLFORM(db.sale, submit_button=T('Sell'), buttons=[(TAG.button(T('Sell'), _type="submit", _class="btn btn-primary"), A(T('Cancel'), _href=URL('cancel', args=bag.id), _class="btn btn-default"))] )
    form.vars.id_bag = bag.id
    form.vars.subtotal = DQ(subtotal)
    form.vars.taxes = DQ(taxes)
    form.vars.total = DQ(total)
    form.vars.quantity = DQ(quantity)
    form.vars.reward_points = reward_points
    form.vars.id_store = bag.id_store.id

    payments = db(db.payment.id_bag == bag.id).select()

    payment_options = db(db.payment_opt.is_active == True).select()
    payments_toolbar = DIV(_class='btn-toolbar btn-justified', _role="toolbar")
    payments_select = DIV(_class="btn-group", _role="group", _id="payment_options")
    payments_lists = DIV(DIV(H3(T('User Wallet')),
         DIV(_id="payments_list_user_wallet")
         , _hidden=True, _id="payments_list_container_user_wallet"
         )
    )
    for payment_option in payment_options:
        classes = "btn-primary" if payment_option == payment_options.first() else ""
        payments_select.append(A(payment_option.name, _class='payment_opt btn btn-default ' + classes, _value=payment_option.id, _id="payment_opt_%s"%payment_option.id))
        payments_lists.append(
            DIV(H3(payment_option.name),
                DIV(_id="payments_list_%s" % payment_option.id)
            , _hidden=True, _id="payments_list_container_%s" % payment_option.id
            )
        )
    payments_toolbar.append(payments_select)
    payments_toolbar.append(DIV(A(I(_class="fa fa-plus"), _class="btn btn-default"), _class="btn-group", _role="group", _id="add_payment"))
    payments_row = DIV( payments_toolbar, INPUT(_name='payments_data', _hidden=True), payments_lists)
    form[0].insert(-1, sqlform_field('payments', 'Payments', payments_row))
    form[0].insert(0, sqlform_field('', T('Reward Points'), reward_points))
    form[0].insert(0, sqlform_field('', T('Quantity'), quantity))
    form[0].insert(0, sqlform_field('', T('Total'), total))
    form[0].insert(0, sqlform_field('', T('Taxes'), taxes))
    form[0].insert(0, sqlform_field('', T('Subtotal'), subtotal))

    if form.process(onvalidation=validate_sale_form).accepted:
        sale = db.sale(form.vars.id)
        # set sale parameters
        store = db(db.store.id == session.store).select(for_update=True).first()
        sale.consecutive = db.store(session.store).consecutive
        store.consecutive += 1;
        store.update_record()

        sale.update_record()
        db.sale_log.insert(id_sale=sale.id, sale_event="paid")

        # set the newly created sale as the payments id_sale
        for payment in db(db.payment.id_bag == sale.id_bag.id).select():
            payment.id_sale = sale.id
            payment.update_record()

        response.flash = T('Sale created')
        if not auth.has_membership('Sales delivery'):
            redirect(URL('scan_ticket'))
        else:
            if requires_serials:
                redirect(URL('serials', args=sale.id))
            remove_stocks(bag_items)
            db.sale_log.insert(id_sale=sale.id, sale_event="delivered")
            redirect(URL('ticket', args=sale.id, vars={'print_ticket': True}))
    elif form.errors:
        response.flash = T('form has errors')
    return dict(form=form, subtotal=subtotal, taxes=taxes, total=total, quantity=quantity, bag=bag, payments=payments, selected_payment_opt=payment_options.first().id)


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
                    client.id_wallet = db.wallet.insert(balance=total, wallet_code=uuid4())
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
                if not already_added:
                    wallet_code = request.vars.wallet_code or uuid4()
                    id_wallet = db.wallet.insert(balance=total, wallet_code=wallet_code)
                    response.info = T('Sale returned, your wallet code is: ') + wallet_code
                    response.info_btn = {'text': T('Print'), 'ref': URL('wallet', 'print_wallet', args=id_wallet), 'target': 'blank'}

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

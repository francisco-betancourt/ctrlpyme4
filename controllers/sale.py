# -*- coding: utf-8 -*-
#
# Author: Daniel J. Ramirez

import json


def remove_stocks(bag_items):
    for bag_item in bag_items:
        # TODO implement stock removal for bag items with serial number
        if bag_item.id_item.has_serial_number:
            pass
        else:
            stocks, quantity = item_stock(bag_item.id_item, session.store).itervalues()
            quantity = DQ(bag_item.quantity)
            total_buy_price = 0
            wavg_days_in_shelf = 0
            for stock in stocks:
                if not quantity:
                    return
                stock_qty = DQ(stock.quantity) - DQ(bag_item.quantity)
                stock.quantity = max(0, stock_qty)
                stock.update_record()
                quantity = abs(stock_qty)

                # set the buy price and buy date from the selected stock
                purchase_item = db(
                    (db.purchase_item.id_purchase == stock.id_purchase)
                  & (db.purchase_item.id_item == stock.id_item.id)
                    ).select().first()
                total_buy_price += bag_item.quantity * purchase_item.price
                days_since_purchase = (bag_item.created_on - stock.created_on).days
                print "Days since purchase: ", days_since_purchase
                wavg_days_in_shelf += days_since_purchase
            bag_item.total_buy_price = total_buy_price
            bag_item.wavg_days_in_shelf = wavg_days_in_shelf / bag_item.quantity

            bag_item.update_record()



@auth.requires(auth.has_membership('Sales checkout')
            or auth.has_membership('Cashier')
            or auth.has_membership('Admin')
            or auth.has_membership('Manager')
            )
def scan_ticket():
    return dict()


def validate_sale_form(form):
    payments = form.vars.payments_data.split(',')
    total = 0
    for payment in payments:
        if not payment:
            continue
        payment_opt_id, amount, change, account = payment.split(':')
        payment_opt = db.payment_opt(payment_opt_id)
        if not payment_opt:
            continue
        total += DQ(amount)
        if len(account) != 4 and payment_opt.requires_account:
            form.errors.payments_data = T('Some payments require an account')
            return
    if not total >= form.vars.total:
        form.errors.payments_data = T('Payments amount is lower than the total')


@auth.requires(auth.has_membership('Sales checkout')
            or auth.has_membership('Cashier')
            or auth.has_membership('Admin')
            or auth.has_membership('Manager')
            )
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

    return locals()


@auth.requires(auth.has_membership('Sales checkout')
            or auth.has_membership('Cashier')
            or auth.has_membership('Admin')
            or auth.has_membership('Manager')
            )
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
    # get bag items data
    bag_items = db(db.bag_item.id_bag == bag.id).select()
    total = 0
    taxes = 0
    subtotal = 0
    reward_points = 0
    quantity = 0
    requires_serials = False
    for bag_item in bag_items:
        # since created bags does not remove stock, there could be more bag_items than stock items, so we need to check if theres enough stock to satisfy this sale, and if there is not, then we need to notify the seller or user
        stocks, stock_qty = item_stock(bag_item.id_item, session.store).itervalues()
        # if theres no stock the user needs to modify the bag
        if stock_qty <= quantity:
            print "not stock"
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

    form = SQLFORM(db.sale)
    form.vars.id_bag = bag.id
    form.vars.subtotal = DQ(subtotal)
    form.vars.taxes = DQ(taxes)
    form.vars.total = DQ(total)
    form.vars.quantity = DQ(quantity)
    form.vars.reward_points = reward_points
    form.vars.id_store = bag.id_store.id

    payment_options_data = {}

    payment_options = db(db.payment_opt.is_active == True).select()
    payments_toolbar = DIV(_class='btn-toolbar btn-justified', _role="toolbar")
    payments_select = DIV(_class="btn-group", _role="group", _id="payment_options")
    for payment_option in payment_options:
        classes = "btn-primary" if payment_option == payment_options.first() else ""
        payments_select.append(A(payment_option.name, _class='payment_opt btn btn-default ' + classes, _value=payment_option.id, _id="payment_opt_%s"%payment_option.id))

        payment_options_data[str(payment_option.id)] = {'allow_change': payment_option.allow_change, 'name': payment_option.name, 'requires_account':payment_option.requires_account}
    payments_toolbar.append(payments_select)
    payments_toolbar.append(DIV(A(I(_class="fa fa-plus"), _class="btn btn-default"), _class="btn-group", _role="group", _id="add_payment"))
    payments_row = DIV( payments_toolbar, DIV(_id="payments_list"), INPUT(_id="payments_data" ,_name="payments_data", _hidden=True), SCRIPT('var payment_options_data = %s; selected_payment_opt = %s' % (json.dumps(payment_options_data), payment_options.first().id)) )

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

        payments = form.vars.payments_data.split(',')
        total = 0
        # register payments
        for payment in payments:
            if not payment:
                continue
            payment_opt_id, amount, change, account = payment.split(':')
            change = DQ(change or 0)
            account = account or None
            db.payment.insert(id_payment_opt=payment_opt_id, id_sale=sale.id, amount=DQ(amount), change_amount=DQ(change), account=account)
        sale.update_record()
        db.sale_log.insert(id_sale=sale.id, sale_event="paid")

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
    return dict(form=form, subtotal=subtotal, taxes=taxes, total=total, quantity=quantity, bag=bag)


@auth.requires(auth.has_membership('Admin')
            or auth.has_membership('Manager')
            or auth.has_membership('Sales delivery')
            )
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


@auth.requires(auth.has_membership('Admin')
            or auth.has_membership('Manager')
            or auth.has_membership('Sales returns')
            or auth.has_membership('Sales checkout')
            )
def get():
    """
        args:
            sale_id
    """

    sale = db.sale(request.args(0))
    return dict(sale=sale)


@auth.requires(auth.has_membership('Sales returns')
            or auth.has_membership('Manager')
            or auth.has_membership('Admin')
            )
def scan_for_refund():
    return dict()


@auth.requires(auth.has_membership('Sales returns')
            or auth.has_membership('Manager')
            or auth.has_membership('Admin')
            )
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
        Field('returned_items')
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
            # add the credit note items
            for bag_item_id in credit_note_items.iterkeys():
                # add credit note item
                db.credit_note_item.insert(id_bag_item=bag_item_id, quantity=credit_note_items[bag_item_id], id_credit_note=id_new_credit_note)
                # return items to stock
                id_item = bag_items_data[bag_item_id].id_item.id
                buy_price = bag_items_data[bag_item_id].buy_price
                stock_data = ((db.stock.id_purchase == db.purchase.id)
                            & (db.purchase_item.id_purchase == db.purchase.id)
                            & (db.stock.id_item == id_item)
                            & (db.purchase_item.price == buy_price)
                            ).select().first()
                print stock_data
    return locals()


@auth.requires(auth.has_membership('Admin')
            or auth.has_membership('Manager')
            )
def update():
    return common_update('sale', request.args)


@auth.requires(auth.has_membership('Admin')
            or auth.has_membership('Manager')
            )
def delete():
    return common_delete('sale', request.args)



def sale_row(row, fields):
    tr = TR()
    # sale status
    last_log = db(db.sale_log.id_sale == row.id).select().last()
    sale_event = last_log.sale_event if last_log else None
    tr.append(TD(T(sale_event or 'Unknown')))
    for field in fields:
        tr.append(TD(row[field]))
    return tr


@auth.requires(auth.has_membership('Admin')
            or auth.has_membership('Manager')
            )
def index():
    rows = common_index('sale')
    data = super_table('sale', ['consecutive', 'subtotal', 'total'], rows, row_function=sale_row, custom_headers=['Status', 'Invoice number', 'Subtotal', 'Total'])
    return locals()

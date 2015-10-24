# -*- coding: utf-8 -*-
#
# Author: Daniel J. Ramirez

import json


def remove_stocks(bag_items):
    for bag_item in bag_items:
        if bag_item.id_item.has_serial_number:
            pass
        else:
            stocks, quantity = item_stock(bag_item.id_item, session.store).itervalues()
            quantity = DQ(bag_item.quantity)
            for stock in stocks:
                if not quantity:
                    return
                stock_qty = DQ(stock.quantity) - DQ(bag_item.quantity)
                stock.quantity = max(0, stock_qty)
                stock.update_record()
                quantity = abs(stock_qty)



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
            )
def get():
    pass


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
    tr.append(TD(T(last_log.sale_event or 'Unknown')))
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

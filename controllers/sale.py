# -*- coding: utf-8 -*-
#
# Author: Daniel J. Ramirez

import json


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
        payment_id, amount, change, account = payment.split(':')
        total += DQ(amount)
    if total >= form.vars.total:
        print total
    else:
        form.errors.payments_data = T('Payments amount is lower than the total')


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
    # get bag items data
    bag_items = db(db.bag_item.id_bag == bag.id).select()
    total = 0
    taxes = 0
    subtotal = 0
    reward_points = 0
    quantity = 0
    for bag_item in bag_items:
        # since created bags does not remove stock, there could be more bag_items than stock items, so we need to check if theres enough stock to satisfy this sale, and if there is not, then we need to notify the seller or user
        stocks, quantity = item_stock(bag_item.id_item, session.store).itervalues()
        # if theres no stock the user needs to modify the bag
        if quantity <= 0:
            print "not stock"
        subtotal += bag_item.sale_price * bag_item.quantity
        taxes += bag_item.sale_taxes * bag_item.quantity
        total += (bag_item.sale_price + bag_item.sale_taxes) * bag_item.quantity
        quantity += bag_item.quantity
        reward_points += bag_item.id_item.reward_points or 0
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

        payment_options_data[str(payment_option.id)] = {'allow_change': payment_option.allow_change, 'name': payment_option.name}
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
        sale.consecutive = db.store(session.store).consecutive
        # sale.id_bag = bag.id
        # sale.subtotal = DQ(subtotal)
        # sale.total = DQ(total)
        # sale.quantity = DQ(quantity)
        # sale.reward_points = reward_points
        # sale.id_store = session.store
        sale.update_record()

        db.sale_log.insert(id_sale=sale.id, sale_event="paid")

        # TODO: add request for update, to update the store consecutive

        response.flash = T('Sale created')
    elif form.errors:
        response.flash = T('form has errors')
    return dict(form=form, subtotal=subtotal, taxes=taxes, total=total, quantity=quantity, bag=bag)


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


@auth.requires(auth.has_membership('Admin')
            or auth.has_membership('Manager')
            )
def index():
    rows = common_index('sale')
    data = super_table('sale', ['consecutive', 'subtotal', 'total'], rows)
    return locals()

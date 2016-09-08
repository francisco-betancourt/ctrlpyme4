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

from constants import STRIPE_SK, STRIPE_PK
from bag_utils import check_bag_owner, bag_selection_return_format, bag_item_taxes, get_ordered_items_count

precheck()


import stripe
stripe.api_key = STRIPE_SK


def get_valid_order_bag(bag_id):
    bag = db.bag(bag_id)
    if not bag:
        raise HTTP(404)
    if not bag.is_on_hold or db(db.sale_order.id_bag == bag.id).select().first():
        raise HTTP(405)
    if bag.created_by != auth.user.id:
        raise HTTP(401)
    return bag


@auth.requires_membership('Clients')
def select_bag():
    """ args: [id_bag] """

    bag = check_bag_owner(request.args(0))
    return bag_selection_return_format(bag)


@auth.requires_membership('Clients')
def activate_bag():
    """ Reactivate a bag that has been BAG_ORDER_COMPLETED but not paid
        args: [id_bag] """

    bag = check_bag_owner(request.args(0))
    if not bag.status == BAG_ORDER_COMPLETE or bag.is_paid or bag.is_sold:
        raise HTTP(405)
    bag.status = BAG_ACTIVE
    bag.update_record()
    return dict()


@auth.requires_membership('Clients')
def order_complete():
    bag = get_valid_order_bag(request.args(0))

    bag.status = BAG_ORDER_COMPLETE
    bag.update_record()

    return dict(completed=True)


@auth.requires_membership('Clients')
def create():
    """
        args [id_bag]
    """


    bag = get_valid_order_bag(request.args(0))

    stores = db(db.store.is_active == True).select()

    form = SQLFORM(db.sale_order, buttons=[], formstyle="bootstrap", _id="order_form")
    if not bag.is_paid:
        if ENABLE_STRIPE:
            form[0].insert(-1, BUTTON(T('Pay now'), _id="custom_button", _class="btn btn-primary" ))
        form[0].insert(-1, INPUT(_value=T('Pay on store'), _type="submit", _class="btn", _id="pay_on_store_button"))
    else:
        form[0].insert(-1, INPUT(_value=T('Order'), _type="submit", _class="btn btn-primary", _id="order_btn" ))
    if form.process().accepted:
        if bag.stripe_charge_id:
            ch = stripe.Charge.retrieve(bag.stripe_charge_id)
            if not ch:
                raise HTTP(500)
            ch.description = '%s %s' % (T("Sale order"), form.vars.id)
            ch.save()

        sale_order = db.sale_order(form.vars.id)
        sale_order.code = "%s%s"%(sale_order.created_on.strftime('%d%H%m%M%y'), sale_order.id)
        sale_order.id_client = auth.user.id
        sale_order.id_bag = bag.id
        sale_order.update_record()
        session.info = {'text': T("You're order has been created, we will notify you when it's ready"), 'button': {'text': 'View ticket', 'ref': URL('bag', 'ticket', args=bag.id), 'target': 'blank'}
        }
        # remove discounts if the bag was not paid
        if not bag.is_paid:
            bag_subtotal, bag_taxes, bag_total = 0, 0, 0
            bag_items = db(db.bag_item.id_bag == bag.id).select()
            for bag_item in bag_items:
                bag_item.sale_price = bag_item.sale_price + bag_item.discount
                bag_item.discount = 0
                # recalculate bag item taxes
                bag_item.sale_taxes = bag_item_taxes(bag_item, bag_item.sale_price)
                bag_item.update_record()
                bag_subtotal += bag_item.sale_price
                bag_taxes += bag_item.sale_taxes
                bag_total += bag_item.sale_price + bag_item.sale_taxes
            # we also need to update bag data
            bag.subtotal = bag_subtotal
            bag.taxes = bag_taxes
            bag.total = bag_total

        bag.completed = True
        bag.status = BAG_COMPLETE
        bag.id_store = sale_order.id_store
        bag.update_record()


        # email
        subject = T('Thank you for your order')
        order_concept = T('Your order has been processed')
        if bag.is_paid:
            subject = T('Thank you for your purchase')
            order_concept = T('Your purchase has been processed')
        items_list = ''
        for bag_item in db(db.bag_item.id_bag == bag.id).select():
            items_list += str(TR( TD(),
                TD('%s x %s' % (DQ(bag_item.quantity, True, True), bag_item.product_name)),
                TD('$ %s' % DQ(bag_item.sale_price, True))
            ))
        subject = '[%s]: %s' % (COMPANY_NAME, subject)
        email_msg = ORDER_EMAIL_CONTENT.format(code=sale_order.code, user_name='%s %s' % (auth.user.first_name, auth.user.last_name), items=items_list, total=str(DQ(bag.total, True)), order_concept=order_concept )
        email_msg = BASE_BRANDED_EMAIL.format(content=email_msg)
        email_msg = '<html>' + email_msg + '</html>'
        # send receipt email
        r = mail.send(to=[auth.user.email], subject=subject, message=email_msg)


        redirect(URL('default', 'index'))
    elif form.errors:
        if form.errors.id_store:
            response.flash = T('Please select a store')

    show_total_without_discounts = True
    return locals()


def pay_and_order():
    """ Charge the credit card """

    if not ENABLE_STRIPE:
        return dict(error=T('stripe not available'))

    bag = get_valid_order_bag(request.args(0))
    if not bag.status == BAG_ORDER_COMPLETE: # commit the bag first
        raise HTTP(400)
    token = request.vars.stripeToken
    if not token:
        raise HTTP(400)

    error = None
    is_stripe_error = True
    try:
        # save customer data
        user = db.auth_user(auth.user.id)
        if not user.stripe_customer_id:
            customer = stripe.Customer.create(
                description="%s %s %s" % (user.first_name, user.last_name, user.email),
                source=token
            )
            user.stripe_customer_id = customer.id
            user.update_record()
        # charge customer
        charge = stripe.Charge.create(
          amount=int(bag.total * 100),
          currency="mxn",
          customer=user.stripe_customer_id
        )
        bag.is_paid = True
        bag.stripe_charge_id = charge.id
        bag.update_record()
        request.vars.stripe_charge_id = charge.id
        return dict(charge_id=charge.id)
    except stripe.error.CardError, e:
        error = e
    except stripe.error.RateLimitError, e:
        # Too many requests made to the API too quickly
        error = e
    except stripe.error.InvalidRequestError, e:
        # Invalid parameters were supplied to Stripe's API
        error = e
    except stripe.error.AuthenticationError, e:
        # Authentication with Stripe's API failed
        # (maybe you changed API keys recently)
        error = e
    except stripe.error.APIConnectionError, e:
        # Network communication with Stripe failed
        error = e
    except stripe.error.StripeError, e:
        # Display a very generic error to the user, and maybe send
        # yourself an email
        error = e
    except Exception, e:
        import traceback as tb
        tb.print_exc()
        is_stripe_error = False
        error = e
    bag.status = BAG_ACTIVE
    bag.update_record()
    if is_stripe_error:
        error = error.json_body['error']
    return dict(error=error)


def get():
    pass


def get_by_code():
    """ args [sale_order_code]  """
    sale_order = db(db.sale_order.code == request.args(0)).select().first()
    if not sale_order:
        raise HTTP(404)
    return locals()


def validate_ready(form):
    """ Validates if all the items in the order are available """
    is_ready = True
    for bag_item in db(db.bag_item.id_bag == form.vars.id_bag).select():
        quantity = item_stock_qty(bag_item.id_item, session.store)
        is_ready &= (quantity >= bag_item.quantity)

    if not ready:
        form.errors.default = T('Some items are not available')


@auth.requires_membership('Sale orders')
def ready():
    """
        args [order_id]
    """

    import supert
    Supert = supert.Supert()

    order = db.sale_order(request.args(0))
    if not order:
        raise HTTP(404)
    # check if the order items are in stock
    items = []

    def ready_status_format(row, f, global_data):
        quantity = item_stock_qty(row.id_item, session.store)

        order_items_qty = get_ordered_items_count(order.id, row.id_item.id)
        item_ready = quantity >= (row.quantity + order_items_qty)
        global_data['is_ready'] &= item_ready

        if item_ready:
            return I(_class='status-circle bg-success'), SPAN(T('yes')),
        else:
            return I(_class='status-circle bg-danger'), SPAN(T('no')),

    global_data = {'is_ready': True}
    data = Supert.SUPERT(
        db.bag_item.id_bag == order.id_bag.id
        , fields=['product_name', 'quantity',
            dict(
                fields=['id'],
                label_as=T('Ready'),
                custom_format=ready_status_format
            )
        ]
        , options_enabled=False
        , global_data=global_data
        , global_options=[]
    )

    is_ready = global_data['is_ready']

    buttons = [] if is_ready else [A(T('Purchase order'), _class="btn btn-primary", _href=URL('purchase', 'create_from_order', args=order.id))]
    if not buttons and order.id_sale.id_client:
        form = SQLFORM.factory(submit_button=T('Notify buyer'), formstyle='bootstrap')
    elif order.is_for_defered_sale and is_ready:
        buttons = [
            A(
                T('Go to sale'), _class="btn btn-primary",
                _href=URL('sale', 'update', args=order.id_sale.id)
            )
        ]
        form = SQLFORM.factory(buttons=buttons)
    else:
        form = SQLFORM.factory(buttons=buttons)
    if form.process(onvalidation=validate_ready).accepted:
        # notify the user
        mail.send(to=[order.id_client.email], subject='[%s] %s' % (COMPANY_NAME, T('Your order is ready')), message=T('Your order is ready and can be retrieved at the following store %s, be sure to bring your <a href="%s">order ticket</a> with you, since it will be required to verify the order') % (order.id_store.name, URL('bag', 'ticket', args=order.id_bag.id, scheme=True, host=True)) )
    elif form.errors:
        response.flash = form.errors.default

    return locals()


@auth.requires_membership('Sale orders')
def delete():
    return common_delete('sale_order', request.args)


@auth.requires_membership('Sale orders')
def index():
    import supert
    Supert = supert.Supert()

    def order_options(row):
        buttons = ()
        if row.is_for_defered_sale:
            buttons += supert.OPTION_BTN(
                'receipt', URL(
                    'ticket', 'show_ticket', vars=dict(id_sale=row.id_sale)
                ), _target='_blank'
            ),
        buttons += supert.OPTION_BTN(
            'playlist_add_check', URL('sale_order', 'ready', args=row.id)
        ),

        return buttons


    q = (db.sale_order.id_store == session.store) & (db.sale_order.is_active == True) & (db.sale_order.is_ready == False)
    data = Supert.SUPERT(q,
        fields=['is_ready', 'is_for_defered_sale', 'created_on'],
        options_func=order_options , global_options=[],
        searchable=False
    )
    return locals()

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

    form = SQLFORM(db.sale_order, submit_button=T('Order'), formstyle="bootstrap")
    if form.process().accepted:
        ch = stripe.Charge.retrieve(bag.stripe_charge_id)
        if not ch:
            raise HTTP(500)
        ch.description = '%s %s' % (T("Sale order"), form.vars.id)
        ch.save()

        sale_order = db.sale_order(form.vars.id)
        sale_order.id_client = auth.user.id
        sale_order.id_bag = bag.id
        sale_order.update_record()
        session.info = {'text': T("You're order has been created, we will notify you when it's ready"), 'button': {'text': 'View ticket', 'ref': URL('bag', 'ticket', args=bag.id), 'target': 'blank'}
        }
        bag.completed = True
        bag.status = BAG_COMPLETE
        bag.update_record()
        redirect(URL('default', 'index'))
    elif form.errors:
        if form.errors.id_store:
            response.flash = T('Please select a store')

    return locals()


def pay_and_order():
    """ Charge the credit card """
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
        if not auth.user.stripe_customer_id:
            customer = stripe.Customer.create(
                description="%s %s %s" % (auth.user.first_name, auth.user.last_name, auth.user.email),
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


def validate_ready(form):
    """ Validates if all the items in the order are available """
    ready == True
    for bag_item in db(db.bag_item.id_bag == form.vars.id_bag).select():
        stock, quantity = item_stock(bag_item.id_item, session.store).itervalues()
        ready &= (quantity >= bag_item.quantity)

    if not ready:
        form.errors.default = T('Some items are not available')


@auth.requires_membership('Sale orders')
def ready():
    """
        args [order_id]
    """

    order = db.sale_order(request.args(0))
    if not order:
        raise HTTP(404)
    ready = True
    # check if the order items are in stock
    items = []
    for bag_item in db(db.bag_item.id_bag == order.id_bag.id).select():
        stock, quantity = item_stock(bag_item.id_item, session.store).itervalues()
        # consider previous orders
        order_items = db(
            (db.sale_order.id_bag == db.bag.id)
            & (db.bag_item.id_bag == db.bag.id)
            & (db.sale_order.id < order.id)
            & (db.sale_order.is_active == True)
            & (db.sale_order.id_sale == None)
            & (db.sale_order.id_store == session.store)
            & (db.bag_item.id_item == bag_item.id_item.id)
        ).select()

        order_items_qty = 0
        for order_item in order_items:
            order_items_qty += order_item.bag_item.quantity

        item_ready = (quantity >= bag_item.quantity + order_items_qty)
        ready &= item_ready
        items.append(dict(bag_item=bag_item, ready=item_ready))

    buttons = [] if ready else [A(T('Purchase order'), _class="btn btn-primary", _href=URL('purchase', 'create_from_order', args=order.id))]
    if not buttons:
        form = SQLFORM.factory(submit_button=T('Notify buyer'), formstyle='bootstrap')
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
def client_order_options(row):
    td = TD()

    # view ticket
    td.append(option_btn('check', ))
    return td


@auth.requires_membership('Sale orders')
def index():
    q = (db.sale_order.id_store == session.store) & (db.sale_order.is_active == True) & (db.sale_order.is_ready == False)
    data = SUPERT(q, fields=['is_ready', 'is_for_defered_sale', 'created_on'], options_func=lambda row: OPTION_BTN('playlist_add_check', URL('sale_order', 'ready', args=row.id) ))
    return locals()

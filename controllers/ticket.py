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


from bag_utils import get_valid_bag, check_bag_owner
import item_utils


def ticket_store_data(store):
    store_data = P()
    if store:
        store_data.append(T('Store') + ': %s' % store.name)
        store_data.append(BR())
        store_data.append("%s %s %s %s %s %s %s %s" % (
            store.id_address.street
            , store.id_address.exterior
            , store.id_address.interior
            , store.id_address.neighborhood
            , store.id_address.city
            , store.id_address.municipality
            , store.id_address.state_province
            , store.id_address.country
        ))
    return store_data


def ticket_item_list(items, concept=''):
    """ creates a table of items, if concept is specified, ignores the items list and uses concept as a unique item in the table, the table will be something like
        QTY  CONCEPT                                           PRICE
        --   <concept>                                         $ --
    """
    items_list = TBODY()

    # items_list.append(HR())
    subtotal = D(0)
    disable_taxes_list = False
    taxes = {}
    taxes_percentages = {}
    total = D(0)
    items = [] if not items else items
    if concept:
        items_list.append(TR(
            TD('--', _class="qty"), TD(concept, _class="name"),
            TD('--'),
            TD('$ --', _class="price"),
            _class="item"
        ))
    else:
        for item in items:
            # assume bag items are being received
            bag_item = item
            # TODO find a better way to identify if the list contains bag items or credit note items
            try:
                item.product_name
            except AttributeError:
                bag_item = item.id_bag_item
            if not bag_item:
                continue
            item_name = bag_item.product_name
            if bag_item.id_item.traits:
                for trait in bag_item.id_item.traits:
                    item_name += ' ' + trait.trait_option
            item_price = bag_item.sale_price
            item_barcode = item_utils.item_barcode(bag_item.id_item)
            # get item taxes
            try:
                if bag_item.item_taxes:
                    taxes_str = bag_item.item_taxes.split(',')
                    for tax_str in taxes_str:
                        tax_name, tax_percentage = tax_str.split(':')
                        if not taxes_percentages.has_key(tax_name):
                            taxes_percentages[tax_name] = DQ(tax_percentage, True, normalize=True)
                        if not taxes.has_key(tax_name):
                            taxes[tax_name] = 0
                        taxes[tax_name] += item_price * (D(tax_percentage) / DQ(100.0))
            except:
                disable_taxes_list = True
            subtotal += item_price
            total += item_price + bag_item.sale_taxes
            item_quantity = DQ(item.quantity, True, normalize=True)
            item_price = DQ(item_price, True)

            items_list.append(TR(
                TD(item_quantity, _class="qty"),
                TD(item_barcode, _class="bc"),
                TD(item_name, _class="name"),
                TD('$ %s' % item_price, _class="price"),
                _class="item"
            ))

    items_list = TABLE(
        THEAD(TR(
            TH(T('QTY'), _class="qty"),
            TH(T('COD'), _class="qty"),
            TH(T('CONCEPT'), _class="name"),
            TH(T('PRICE'), _class="price"),
            _class="item"
        )),
        items_list,
        _id="items_list"
    )

    if disable_taxes_list:
        taxes = {}
        taxes_percentages = {}

    return items_list, subtotal, total, taxes, taxes_percentages


def ticket_taxes_data(taxes, taxes_percentages):
    taxes_data = []
    for key in taxes.iterkeys():
        text = '%s %s %%: $ %s' % (key, taxes_percentages[key], DQ(taxes[key], True))
        taxes_data.append(text)
    return taxes_data


def ticket_total_data(totals):
    total_data = DIV(_id="total_data")
    for total in totals:
        total_data.append(DIV(total))
    return total_data


def ticket_payments_data(payments, include_payment_date=False):
    """ ticket format for a list of payments """

    payments_data = DIV(_id="payments_data")
    change = 0
    for payment in payments:
        payment_name = payment.id_payment_opt.name
        if include_payment_date:
            payment_name = '%s %s ' % (payment.created_on, payment_name)
        if payment.id_payment_opt.requires_account:
            payment_name += ' %s' % payment.account
        change += payment.change_amount
        payments_data.append(
            DIV('%s : $ %s' % (payment_name, DQ(payment.amount, True)) )
        )
    payments_data.append(DIV('%s : $ %s' % (T('change'), DQ(change, True))))

    return payments_data


def mini_ticket_format(title, content=None, barcode="", date=None):
    """ Used to create ticket extra data, basically appending multiple tickets into one """
    return DIV(
        DIV(P(title), P(date), _class="right head"),
        content,
        DIV(_id="barcode%s" % barcode, _class="barcode"),
        SCRIPT(_type="text/javascript", _src=URL('static','js/jquery-barcode.min.js')),
        SCRIPT('$("#barcode%s").barcode({code: "%s", crc: false}, "code39");' % (barcode, barcode)),
        _class="extra-ticket"
    )


def ticket_format(store_data=None, title="", content=None, barcode="", footer=None, date=None):
    return DIV(
        P(IMG(_class="logo", _src=COMPANY_LOGO_URL)),
        DIV(P(COMPANY_NAME), P(title), P(date), _class="right head"),
        content,
        store_data,
        P(MARKMIN(TICKET_FOOTER), _id="ticket_footer"),
        DIV(footer),
        DIV(_id="barcode", _class="barcode"),
        SCRIPT(_type="text/javascript", _src=URL('static','js/jquery-barcode.min.js')),
        SCRIPT('$("#barcode").barcode({code: "%s", crc: false}, "code39");' % barcode),
        _id="ticket", _class="ticket"
    )


def credit_note_ticket_data(credit_note):
    items = db(
        (db.credit_note_item.id_credit_note == credit_note.id)
    ).select()
    concept = None if items else T('Defered sale')

    items_list, subtotal, total, taxes, taxes_percentages = ticket_item_list(items, concept)

    payments_data = DIV(
        DIV('%s : $ %s' % ('total', DQ(credit_note.total, True)) ),
        _id='payments_data'
    )
    return dict(items_list=items_list, payments_data=payments_data)


def credit_note_ticket(id_credit_note):
    if not auth.has_membership('Sales returns'):
        raise HTTP(404)

    credit_note = db.credit_note(id_credit_note)
    if not credit_note:
        raise HTTP(404)

    if MERGE_CREDIT_NOTES_IN_SALE:
        return sale_ticket(credit_note.id_sale)

    store_data = ticket_store_data(credit_note.id_sale.id_store)
    data = credit_note_ticket_data(credit_note)
    items_list = data['items_list']
    payments_data = data['payments_data']

    return ticket_format(
        store_data, T('Credit note'),
        DIV(items_list, payments_data),
        credit_note.code, P(T('')),
        date=credit_note.created_on
    )


def sale_ticket(id_sale):
    if not auth.has_membership('Sales checkout'):
        raise HTTP(404)
    sale = db.sale(id_sale)
    store_data = ticket_store_data(sale.id_store)
    items = db( (db.bag_item.id_bag == sale.id_bag.id) ).select()

    items_list, subtotal, total, taxes, taxes_percentages = ticket_item_list(items)

    payments = db(db.payment.id_sale == sale.id).select()
    payments_data = ticket_payments_data(payments, sale.is_deferred)
    totals = [ '%s : $ %s' % (T('subtotal'), DQ(sale.subtotal, True)) ]
    totals += ticket_taxes_data(taxes, taxes_percentages)
    totals += [ '%s : $ %s' % (T('total'), DQ(sale.total, True)) ]
    total_data = ticket_total_data(totals)

    credit_notes_tickets = DIV()
    if MERGE_CREDIT_NOTES_IN_SALE:
        credit_notes = db(
            (db.credit_note.id_sale == sale.id) &
            (db.credit_note.is_usable == True)
        ).iterselect()
        for credit_note in credit_notes:
            credit_note_data = credit_note_ticket_data(credit_note)
            credit_notes_tickets.append(mini_ticket_format(
                T('Credit note'),
                DIV(
                    credit_note_data['items_list'],
                    credit_note_data['payments_data']
                ),
                credit_note.code,
                date=credit_note.created_on
            ))

    return ticket_format(store_data, T('Sale'),
        DIV(
            DIV(items_list, total_data, payments_data),
            credit_notes_tickets
        ),
        "%010d" % sale.id, '', date=sale.modified_on
    )


def bag_ticket(id_bag):
    if not (auth.has_membership('Sales bags') or auth.has_membership('Clients')):
        raise HTTP(404)

    bag = check_bag_owner(id_bag)
    if not bag:
        raise HTTP(404)
    store_data = ticket_store_data(bag.id_store)
    items = db( (db.bag_item.id_bag == bag.id) ).select()

    items_list, subtotal, total, taxes, taxes_percentages = ticket_item_list(items)

    totals = [ '%s : $ %s' % (T('subtotal'), DQ(bag.subtotal, True)) ]
    totals += ticket_taxes_data(taxes, taxes_percentages)
    totals += [ '%s : $ %s' % (T('total'), DQ(bag.total, True)) ]
    total_data = ticket_total_data(totals)

    return ticket_format(store_data, T('Bag'),
        DIV(items_list, total_data),
        "%010d" % bag.id, '', date=bag.modified_on
    )


def stock_transfer_ticket(id_stock_transfer):
    if not auth.has_membership('Stock transfers'):
        raise HTTP(404)
    stock_transfer = db.stock_transfer(id_stock_transfer)
    bag = stock_transfer.id_bag
    store_data = ticket_store_data(stock_transfer.id_store_from)
    items = db( (db.bag_item.id_bag == bag.id) ).select()

    items_list, subtotal, total, taxes, taxes_percentages = ticket_item_list(items)

    title = "%s - %s -> %s" % (T('Stock transfer'), stock_transfer.id_store_from.name, stock_transfer.id_store_to)
    return ticket_format(store_data, title,
        items_list,
        "%010d" % stock_transfer.id, P(T('')), date=stock_transfer.created_on
    )



def get():
    """ simply redirect the user to the ticket view
        args: [next_url]
    """

    next_url = request.vars.next_url
    if request.vars.next_url:
        del request.vars.next_url
    session.ticket_url = URL('show_ticket', vars=request.vars)
    url = URL('default', 'index')
    if next_url:
        url = next_url
    elif request.env.http_referer:
        url = request.env.http_referer
    redirect( url )


def show_ticket():
    """ vars: [id_credit_note, id_sale, id_bag, id_stock_transfer] """

    ticket_html = None
    if request.vars.id_credit_note:
        ticket_html = credit_note_ticket(request.vars.id_credit_note)
    elif request.vars.id_sale:
        ticket_html = sale_ticket(request.vars.id_sale)
    elif request.vars.id_bag:
        ticket_html = bag_ticket(request.vars.id_bag)
    elif request.vars.id_stock_transfer:
        ticket_html = stock_transfer_ticket(request.vars.id_stock_transfer)

    return dict(ticket=ticket_html)

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


expiration_redirect()

import wallet_utils


@auth.requires_membership("Clients management")
def print_wallet():
    """ args: [wallet_id] """

    wallet = db.wallet(request.args(0))
    if not wallet:
        session.info = T("Wallet not found")
        redirect(URL('default', 'index'))

    return locals()



@auth.requires_membership("Clients management")
def get_by_code():
    """
        args: [wallet_code]
    """
    wallet = db(db.wallet.wallet_code == request.args(0)).select().first()
    if not wallet:
        raise HTTP(404)

    return dict(
        wallet=wallet
    )



@auth.requires_membership("Manager")
def merge_wallets():
    """ Merge wallet_2 into wallet_1, removing the balance from wallet_2 and adding it to wallet_1
        args[id_wallet_1, id_wallet_2]
    """
    w1 = db(db.wallet.id == request.args(0)).select(for_update=True).first()
    w2 = db(db.wallet.id == request.args(1)).select(for_update=True).first()

    if not (w1 and w2):
        session.info = T('Wallet not found')
        redirect(URL('index', args=w1.id))
    if w1.id == w2.id:
        session.info = T('The specified wallets are the same')
        redirect(URL('index', args=w1.id))

    _w, amount = wallet_utils.transaction(
        w2.balance, wallet_utils.CONCEPT_WALLET_MERGE,
        ref=w2.id, wallet=w1
    )
    wallet_utils.transaction(
        -amount, wallet_utils.CONCEPT_WALLET_MERGE,
        ref=w1.id, wallet=w2
    )

    session.info = T(
        'Transaction done, added $ %s to the specified wallet.'
    ) % (DQ(b, True))

    redirect(URL('index', args=w1.id))


@auth.requires_membership("Admin config")
def add_money():
    """ Add or remove money to a specified wallet """

    qty = 0
    try:
        qty = D(request.vars.amount)
    except:
        session.info = T('Invalid amount')
        redirect(URL('index', args=wallet.id))

    wallet, amount = wallet_utils.transaction(
        qty, wallet_utils.CONCEPT_ADMIN, wallet_id=request.args(0)
    )

    msg = '$ %s added to wallet.'
    if qty < 0:
        msg = '$ %s removed from wallet.'
    qty = DQ(abs(qty), True)

    session.info = T(msg) % qty
    redirect(URL('index', args=wallet.id))



@auth.requires_membership("Clients management")
def index():
    """ args [wallet_id] """

    import supert
    Supert = supert.Supert()

    wallet = db.wallet(request.args(0))
    if not wallet:
        session.info = T("Wallet not found")
        redirect(URL('default', 'index'))

    clients = db(
        (db.auth_user.is_client == True) &
        (db.auth_user.id_wallet != wallet.id)
    ).iterselect(
        orderby=db.auth_user.first_name|db.auth_user.last_name
    )


    def concept_format(row, fields):
        text = ""
        href = None
        if row.concept == wallet_utils.CONCEPT_PAYMENT:
            sale_id = db(db.payment.id == row.ref_id).select().first().id_sale.id
            text += T('Sale') + ' %s' % sale_id
            href = URL('ticket', 'show_ticket', vars={"id_sale": sale_id})
        elif row.concept == wallet_utils.CONCEPT_CREDIT_NOTE:
            text += T('Credit note') + ' %s' % row.ref_id
            href = URL('ticket', 'show_ticket', vars={"id_credit_note": row.ref_id})
        elif row.concept == wallet_utils.CONCEPT_SALE_REWARD:
            text += T('sale reward') + ' %s' % row.ref_id
            href = URL('ticket', 'show_ticket', vars={"id_sale": row.ref_id})
        elif row.concept == wallet_utils.CONCEPT_ADMIN:
            text += T('Admin')
        elif row.concept == wallet_utils.CONCEPT_WALLET_MERGE:
            text += T('Wallet merge') + ' %s' % row.ref_id


        if href:
            return A(text, _href=href, _target='_blank')
        else:
            return text


    def created_by_format(row, fields):
        if row[fields[0]]:
            cb = row[fields[0]]
            return "%s %s" % (cb.first_name, cb.last_name)
        else:
            return T('SYSTEM')
    def amount_format(row, fields):
        amount = row[fields[0]]
        style = "text-success"
        if amount < 0:
            style = "text-danger"

        return B(DQ(amount, True), _class=style)


    query = (db.wallet_transaction.id_wallet == wallet.id)
    transactions_table = Supert.SUPERT(
        query, select_args={"orderby": ~db.wallet_transaction.created_on},
        fields=[
            dict(
                fields=['concept'],
                custom_format=concept_format
                , label_as=T('Concept')
            ),
            dict(
                fields=['amount'],
                custom_format=amount_format
                , label_as=T('Amount')
            ),
            dict(
                fields=['created_by'],
                custom_format=created_by_format
                , label_as=T('Created by')
            ),
            'created_on'
        ], options_enabled=False, selectable=False, global_options=[],
        searchable=False
    )


    return dict(wallet=wallet, clients=clients,
        transactions_table=transactions_table
    )

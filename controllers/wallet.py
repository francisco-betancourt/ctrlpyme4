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


#
# def get():
#     """
#         args: [wallet_id]
#     """
#
#     return dict(wallet=db.wallet(request.args(0)))
#
#
# def get_user_wallet():
#     """
#         args: [user_id]
#     """
#
#     user = db.auth_user(request.args(0))
#     print user
#     if not user:
#         raise HTTP(404)
#     return dict(wallet=db.wallet(user.id_wallet))
#
#

#
#


expiration_redirect()

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



@auth.requires_membership("Clients management")
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

    b = w2.balance
    w1.balance += b
    w2.balance = 0
    w1.update_record()
    w2.update_record()

    session.info = T(
        'Transaction done, added $ %s to the specified wallet.'
    ) % (DQ(b, True))

    redirect(URL('index', args=w1.id))



@auth.requires_membership("Clients management")
def index():
    """ args [wallet_id] """

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


    return dict(wallet=wallet, clients=clients)

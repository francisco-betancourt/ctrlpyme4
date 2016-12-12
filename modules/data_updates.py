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


# This module is used to update specific data when there are changes in the
# database that need to be retroactive
#


from gluon import current
from gluon.storage import Storage
import wallet_utils
import common_utils


def update_stock_item_removals():
    """ Update stock item removals when they have missing auth.signature data and no store
    """
    db = current.db

    for sir in db(db.stock_item_removal.id > 0).iterselect():
        sir.id_store = sir.id_stock_item.id_store.id
        if sir.id_bag_item:
            sir.created_on = sir.id_bag_item.id_bag.created_on
            sir.modified_on = sir.id_bag_item.id_bag.modified_on
            sir.created_by = sir.id_bag_item.id_bag.created_by
            sir.modified_by = sir.id_bag_item.id_bag.modified_by
        elif sir.id_inventory_item:
            sir.created_on = sir.id_inventory_item.id_inventory.created_on
            sir.modified_on = sir.id_inventory_item.id_inventory.modified_on
            sir.created_by = sir.id_inventory_item.id_inventory.created_by
            sir.modified_by = sir.id_inventory_item.id_inventory.modified_by
        sir.update_record()


def update_to_wallet_transactions():
    """ Add wallet transactions previously unavailable, this function will
        only consider the credit notes and payments, rewards points will not be
        added.
    """

    db = current.db

    db(
        (db.wallet_transaction.concept == wallet_utils.CONCEPT_CREDIT_NOTE) |
        (db.wallet_transaction.concept == wallet_utils.CONCEPT_PAYMENT)
    ).delete()

    for credit_note in db(db.credit_note.id > 0).iterselect():
        try:
            wallet_utils.transaction(
                credit_note.total, wallet_utils.CONCEPT_CREDIT_NOTE,
                ref=credit_note.id, wallet_code=credit_note.code,
                is_system_op=True, created_by=credit_note.created_by.id,
                now=credit_note.created_on
            )
        except:
            print "ERROR with credit note: ", credit_note.id


    payments = db(
        (db.payment.id_sale == db.sale.id) &
        (db.sale.is_done == True) &
        (db.payment.id_payment_opt == common_utils.get_wallet_payment_opt())
    ).iterselect(db.payment.ALL)
    for payment in payments:
        try:
            wallet_utils.transaction(
                -payment.amount, wallet_utils.CONCEPT_PAYMENT,
                ref=payment.id, wallet_code=payment.wallet_code,
                is_system_op=True, created_by=payment.created_by.id,
                now=payment.created_on
            )
        except Exception as e:
            print e
            print "ERROR with payment: ", payment.id

    for wallet in db(db.wallet.id > 0).iterselect():
        s = db.wallet_transaction.amount.sum()
        balance = db(
            db.wallet_transaction.id_wallet == wallet.id
        ).select(s).first()[s] or 0
        wallet.balance = balance
        wallet.update_record()
        client = db(
            (db.auth_user.id_wallet == wallet.id) &
            (db.auth_user.is_client == True)
        ).select().first()
        if not client:
            client = Storage(first_name="???", last_name='???')
        print "{first_name} {last_name}, {wallet_code}, {new_balance}".format(
            first_name=client.first_name, last_name=client.last_name,
            wallet_code=wallet.wallet_code, new_balance=wallet.balance
        )

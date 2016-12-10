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

from uuid import uuid4


CONCEPT_SYSTEM_OP = -1000  # transaction performed by system fixes
CONCEPT_SYSTEM = 0  # transaction performed by the system
CONCEPT_PAYMENT = 1  # removed by payment
CONCEPT_UNDO_PAYMENT = -1
CONCEPT_CREDIT_NOTE = 2  # added via credit note
CONCEPT_SALE_REWARD = 3  # reward points for sale
CONCEPT_ADMIN = 4   # performed by the instance admin or instance staff
CONCEPT_WALLET_MERGE = 5   # merge of two wallets
CONCEPT_SALE_REFUND = 6   # merge of two wallets

CONCEPTS = [
    CONCEPT_SYSTEM, CONCEPT_PAYMENT, CONCEPT_CREDIT_NOTE, CONCEPT_SALE_REWARD,
    CONCEPT_ADMIN, CONCEPT_UNDO_PAYMENT, CONCEPT_SYSTEM_OP,
    CONCEPT_WALLET_MERGE, CONCEPT_SALE_REFUND
]


def get_random_wallet_code():
    return str(uuid4()).split('-')[0] # is this random enough?


def new(balance=0):
    db = current.db

    wallet_code = get_random_wallet_code()
    return db.wallet.insert(wallet_code=wallet_code, balance=balance)



def transaction(amount, concept, ref=None, wallet_id=None, wallet_code=None, wallet=None):
    """ Creates a wallet transaction for the wallet that belongs to the specified wallet_id or wallet_code, transactions are used to keep a record of every wallet operation.
    """
    db = current.db

    if not wallet:
        query = db.wallet.id == wallet_id if wallet_id else db.wallet.wallet_code == wallet_code

        wallet = db(query).select(for_update=True).first()

    if not concept in CONCEPTS:
        raise CP_WalletTransactionError("invalid concept")
    if not wallet:
        raise CP_WalletTransactionError("wallet not found")

    # in case of undo we have to remove transactions associated with the reference
    if concept == CONCEPT_UNDO_PAYMENT:
        # undo transaction
        for transaction in db(
            (db.wallet_transaction.id_wallet == wallet.id) &
            (db.wallet_transaction.ref == wallet_transaction.ref) &
            (db.wallet_transaction.concept == CONCEPT_PAYMENT)
        ).iterselect():
            p_amount += transaction.amount
            wallet.balance -= transaction.amount
            transaction.delete_record()
    else:
        # fix removal amount when the concept is a common operation
        if concept != CONCEPT_SYSTEM_OP and amount < 0:
            amount = min(wallet.balance, abs(amount))

        db.wallet_transaction.insert(
            id_wallet=wallet.id,
            amount=amount,
            concept=concept,
            ref_id=ref
        )

    # create a new transaction
    wallet.balance += amount
    wallet.update_record()

    return wallet, amount



def is_wallet(payment_opt):
    if not payment_opt:
        return False
    return payment_opt.name == 'wallet'


def get_wallet_payment_opt():
    db = current.db

    return db(db.payment_opt.name == 'wallet').select().first()

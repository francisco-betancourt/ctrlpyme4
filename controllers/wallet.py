# -*- coding: utf-8 -*-
#
# Author: Daniel J. Ramirez

def get():
    """
        args:
            wallet_id
    """

    return dict(wallet=db.wallet(request.args(0)))


def get_user_wallet():
    """
        args:
            user_id
    """

    user = db.auth_user(request.args(0))
    print user
    if not user:
        raise HTTP(404)
    return dict(wallet=db.wallet(user.id_wallet))


def get_by_code():
    """
        args:
            wallet_code
    """

    return dict(wallet=db(db.wallet.wallet_code == request.args(0)).select().first())


def print_wallet():
    """
        args:
            wallet_id
    """

    wallet = db.wallet(request.args(0))
    if not wallet:
        raise HTTP(404)

    return locals()


# def update():
#     return common_update('name', request.args)
#
#
# def delete():
#     return common_delete('name', request.args)
#
#
# def index():
#     rows = common_index('name')
#     return locals()

# -*- coding: utf-8 -*-
#
# Author: Daniel J. Ramirez

def settle():
    """ args: [id_account_payable] """
    account_payable = db.account_payable(request.args(0))
    if not account_payable:
        raise HTTP(404)
    account_payable.is_settled = True
    account_payable.update_record()

    session.info = T('Settled debt')
    redirect(URL('index'))


def account_row(row, fields):
    #TODO show remaining days
    tr = TR()
    tr.append(
        TD(
            A(row.id_purchase.id, _href=URL('purchase', 'get', args=row.id_purchase.id), _target="_blank" )
        )
    )
    return tr


def index():
    data = super_table('account_payable', ['id_purchase'], db.account_payable.is_settled == False, row_function=account_row, options_function=lambda row : [option_btn('check', URL('settle', args=row.id), ' settle')])
    return locals()

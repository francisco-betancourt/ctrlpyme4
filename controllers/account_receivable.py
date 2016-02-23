# -*- coding: utf-8 -*-
#
# Author: Daniel J. Ramirez


@auth.requires_membership('Accounts receivable')
def settle():
    """ args: [id_account_receivable] """
    account_receivable = db.account_receivable(request.args(0))
    if not account_receivable:
        raise HTTP(404)
    account_receivable.is_settled = True
    account_receivable.update_record()

    session.info = T('Settled debt')
    redirect(URL('index'))


@auth.requires_membership('Accounts receivable')
def account_row(row, fields):
    #TODO show remaining days
    tr = TR()
    tr.append(
        TD(
            A(row.id_sale.id, _href=URL('sale', 'ticket', args=row.id_sale.id), _target="_blank" )
        )
    )
    return tr


@auth.requires_membership('Accounts receivable')
def index():
    data = super_table('account_receivable', ['id_sale'], db.account_receivable.is_settled == False, row_function=account_row, options_function=lambda row : [option_btn('check', URL('settle', args=row.id), ' settle')])
    return locals()

# -*- coding: utf-8 -*-
#
# Author: Daniel J. Ramirez

@auth.requires_membership('Accounts payable')
def settle():
    """ args: [id_account_payable] """
    account_payable = db.account_payable(request.args(0))
    if not account_payable:
        raise HTTP(404)
    account_payable.is_settled = True
    account_payable.update_record()

    session.info = T('Settled debt')
    redirect(URL('index'))


@auth.requires_membership('Accounts payable')
def index():
    def ar_options(row):
        return OPTION_BTN('receipt', URL('purchase', 'get', args=row.id_purchase.id)), OPTION_BTN('done', URL('settle', args=row.id))
    data = SUPERT(db.account_payable.is_settled == False,
        fields=['id_purchase', 'epd'], options_func=ar_options)
    return locals()

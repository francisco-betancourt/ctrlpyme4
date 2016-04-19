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


precheck()

@auth.requires_membership('Accounts receivable')
def settle():
    """ args: [id_account_receivable] """
    payment = db.payment(request.args(0))
    if payment.is_settled or not payment.id_payment_opt.credit_days:
        raise HTTP(405)
    if not payment:
        raise HTTP(404)
    payment.is_settled = True
    payment.update_record()

    session.info = T('Settled debt')
    redirect(URL('index'))


@auth.requires_membership('Accounts receivable')
def index():
    data = SUPERT(db.payment.is_settled == False, fields=['id_sale.consecutive', 'epd', 'amount'],  options_func=lambda row : [OPTION_BTN('receipt', URL('sale', 'ticket', args=row.id_sale.id)), OPTION_BTN('done', URL('settle', args=row.id))])
    return locals()

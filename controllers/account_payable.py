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

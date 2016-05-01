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

precheck()

@auth.requires_membership('Sales returns')
def get():
    """ args: [id_credit_note] """

    redirect( URL('ticket', 'get', vars=dict(id_credit_note=request.args(0))) )


@auth.requires_membership('Sales returns')
def index():
    data = common_index('credit_note', ['subtotal', 'total', 'created_on'], supert_vars=dict(options_func=lambda row: OPTION_BTN('receipt', URL('credit_note', 'get', args=row.id)) ))

    return locals()

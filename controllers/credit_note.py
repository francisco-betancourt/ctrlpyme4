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

expiration_redirect()
precheck()

@auth.requires_membership('Sales returns')
def get():
    """ args: [id_credit_note] """

    redirect( URL('ticket', 'get', vars=dict(id_credit_note=request.args(0))) )


@auth.requires_membership('Sales returns')
def index():
    import supert

    def client_format(row, fields):
        if row.id_sale and row.id_sale.id_client:
            return "%s %s" % (row.id_sale.id_client.first_name, row.id_sale.id_client.last_name)
        return "--"

    data = common_index(
        'credit_note', [
            'subtotal', 'total', 'created_on',
            dict(
                fields=['id_sale.id_client.first_name', 'id_sale.id_client.last_name'],
                label_as=T('Client'),
                custom_format=client_format
            )
        ], supert_vars=dict(options_func=lambda row: supert.OPTION_BTN('receipt', URL('ticket', 'show_ticket', vars=dict(id_credit_note=row.id)), _target='_blank'), global_options=[] )
    )

    return locals()

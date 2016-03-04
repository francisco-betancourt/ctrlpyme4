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

@auth.requires_membership('Sales returns')
def get():
    """
        args: [id_credit_note]
    """

    credit_note = db.credit_note(request.args(0))
    credit_note_items = db(db.credit_note_item.id_credit_note == credit_note.id).select()

    ticket = create_ticket(T('Credit note'), credit_note.id_sale.id_store, credit_note.created_by, credit_note_items, "", "", sale=credit_note.id_sale)
    return locals()


@auth.requires_membership('Sales returns')
def index():
    data = super_table('credit_note', ['subtotal', 'total'], ((db.credit_note.is_active == True)), options_function=lambda row: [option_btn('', URL('credit_note', 'get', args=row.id), T('View'))]
    )

    return locals()

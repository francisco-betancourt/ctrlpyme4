# -*- coding: utf-8 -*-
#
# Author: Daniel J. Ramirez

@auth.requires_membership('Sales returns')
def get():
    """
        args:
            id_credit_note
    """

    credit_note = db.credit_note(request.args(0))
    credit_note_items = db(db.credit_note_item.id_credit_note == credit_note.id).select()

    ticket = create_ticket(T('Credit note'), credit_note.id_sale.id_store, credit_note.created_by, credit_note_items, "", "")
    return locals()


@auth.requires_membership('Sales returns')
def index():
    data = super_table('credit_note', ['subtotal', 'total'], ((db.credit_note.is_active == True)), options_function=lambda row: [option_btn('', URL('credit_note', 'get', args=row.id), T('View'))]
    )

    return locals()

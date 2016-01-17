# -*- coding: utf-8 -*-
#
# Author: Daniel J. Ramirez

def get():
    """
        args:
            id_credit_note
    """

    credit_note = db.credit_note(request.args(0))
    credit_note_items = db(db.credit_note_item.id_credit_note == credit_note.id).select()

    ticket = create_ticket(T('Credit note'), credit_note.id_sale.id_store, credit_note.created_by, credit_note_items, "", "")
    return locals()

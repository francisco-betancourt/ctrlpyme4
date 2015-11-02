# -*- coding: utf-8 -*-
#
# Author: Daniel J. Ramirez

def get():
    """
        args:
            id_credit_note
    """

    credit_note = db.credit_note(request.args(0))
    return locals()

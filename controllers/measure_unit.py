# -*- coding: utf-8 -*-
#
# Author: Daniel J. Ramirez

def create():
    """ """

    return common_create('measure_unit')


def get():
    pass


def update():
    """
    args: [measure_unit_id]
    """

    return common_update('measure_unit', request.args)


def delete():
    """
    args: [id_1, id_2, ..., id_n]
    """

    common_delete('measure_unit', request.args)


def index():
    measure_units = db((db.measure_unit.id > 0) & (db.measure_unit.is_active == True)).select()

    return locals()

# -*- coding: utf-8 -*-
#
# Author: Daniel J. Ramirez


@auth.requires_membership('Admin')
def create():
    """ """

    return common_create('measure_unit')


@auth.requires_membership('Admin')
def get():
    pass


@auth.requires_membership('Admin')
def update():
    """
    args: [measure_unit_id]
    """

    return common_update('measure_unit', request.args)


@auth.requires_membership('Admin')
def delete():
    """
    args: [id_1, id_2, ..., id_n]
    """

    common_delete('measure_unit', request.args)


@auth.requires_membership('Admin')
def index():
    data = common_index('measure_unit', ['name', 'symbol'])

    return locals()

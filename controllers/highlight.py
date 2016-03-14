# -*- coding: utf-8 -*-
#
# Author: Daniel J. Ramirez

@auth.requires_membership('Highlights')
def create():
    return common_create('highlight')


@auth.requires_membership('Highlights')
def update():
    return common_update('highlight', request.args)


@auth.requires_membership('Highlights')
def delete():
    return common_delete('highlight', request.args)


@auth.requires_membership('Highlights')
def index():
    data = common_index('highlight', ['title'])
    return locals()

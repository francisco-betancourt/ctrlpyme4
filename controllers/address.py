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

expiration_redirect()

@auth.requires_membership('Safe config')
def create():
    form = SQLFORM(db.address)
    if form.process().accepted:
        response.flash = T('form accepted')
        if request.vars._next:
            request.vars._next += '/%s' % form.vars.id
        redirection()
    elif form.errors:
        response.flash = T('form has errors')
    return dict(form=form)


@auth.requires_membership('Config')
def get():
    pass

@auth.requires_membership('Config')
def update():
    return common_update('address',request.args)


@auth.requires_membership('Config')
def delete():
    common_delete('address',request.args)


@auth.requires_membership('Config')
def address_row(row, fields):
    address = ""
    for field in fields:
        address += row[field] + ' '
    return TR(TD(address))


@auth.requires_membership('Config')
def index():
    """ """

    title = T('addresses')
    data = common_index('address', [
        {'fields': ['street', 'exterior', 'interior'], 'label_as': T('Address') }, 'neighborhood', 'postal_code', 'municipality', 'state_province'
    ] )
    return locals()

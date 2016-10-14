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


@auth.requires(
       auth.has_membership('Purchases')
    or auth.has_membership('Admin')
    or auth.has_membership('Manager')
)
def create():
    """ args: [id_address] """
    address = db.address(request.args(0))
    if not address:
        redirect(URL('address', 'create', vars=dict(_next=URL('create'))))
    form = SQLFORM(db.supplier)
    form.vars.id_address = address.id
    if form.process().accepted:
        # insert store group
        response.flash = T('form accepted')
        redirect(URL('index'))
    elif form.errors:
        response.flash = T('form has errors')
    return dict(form=form)


@auth.requires(
       auth.has_membership('Purchases')
    or auth.has_membership('Admin')
    or auth.has_membership('Manager')
)
def get():
    pass


@auth.requires(
       auth.has_membership('Purchases')
    or auth.has_membership('Admin')
    or auth.has_membership('Manager')
)
def update():
    return common_update('supplier', request.args)


@auth.requires(
       auth.has_membership('Purchases')
    or auth.has_membership('Admin')
    or auth.has_membership('Manager')
)
def delete():
    return common_delete('supplier', request.args)


@auth.requires(
       auth.has_membership('Purchases')
    or auth.has_membership('Admin')
    or auth.has_membership('Manager')
)
def index():
    data = common_index('supplier', ['business_name', 'tax_id'])
    return locals()

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


@auth.requires_membership('Items management')
def create():
    return common_create('trait_category')


@auth.requires_membership('Items management')
def get():
    trait_category = db.trait_category(request.args(0))
    redirect(URL('trait', 'index', vars={'trait_category': trait_category.id}))


@auth.requires_membership('Items management')
def update():
    return common_update('trait_category', request.args)


@auth.requires_membership('Items management')
def delete():
    return common_delete('trait_category', request.args)


@auth.requires_membership('Items management')
def index():
    import supert

    data = common_index('trait_category', ['name'], dict(options_func=lambda row: supert.supert_default_options(row) + (supert.OPTION_BTN('details', URL('get', args=row.id), title=T('values')),) ) )
    return locals()


@auth.requires_membership('Items management')
def search():
    """ args: [term] """

    if not request.raw_args:
        raise HTTP(404)

    term = request.raw_args.split('/')[0] or ''
    match = db(db.trait_category.name.contains(term)).iterselect(
        db.trait_category.name, db.trait_category.id
    )

    return dict(match=match)

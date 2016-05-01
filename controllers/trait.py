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
    trait_category = db.trait_category(request.vars.trait_category)
    if not trait_category:
        raise HTTP(400)

    form = SQLFORM(db.trait, fields=['trait_option'])
    form.vars.id_trait_category = trait_category.id
    if form.process().accepted:
        response.flash = 'form accepted'
        redirect(URL('trait_category', 'get', args=trait_category.id))
    elif form.errors:
        response.flash = 'form has errors'
    return dict(form=form)


@auth.requires_membership('Items management')
def update():
    trait = db.trait(request.args(0))
    if not trait:
        raise HTTP(400)

    form = SQLFORM(db.trait, trait, fields=['trait_option'])
    if form.process().accepted:
        response.flash = 'form accepted'
        redirect(URL('trait_category', 'get', args=trait.id_trait_category))
    elif form.errors:
        response.flash = 'form has errors'
    return dict(form=form)


@auth.requires_membership('Items management')
def index():
    trait_category = db.trait_category(request.vars.trait_category)
    if not trait_category:
        raise HTTP(400)

    query = (db.trait.is_active == True) & (db.trait.id_trait_category == trait_category.id)
    data = SUPERT(query, fields=['trait_option'])

    return locals()


@auth.requires_membership('Items management')
def delete():
    if not request.vars.trait_category:
        raise HTTP(400)
    if not request.args:
        raise HTTP(400)
    query = (db['trait'].id < 0)
    for arg in request.args:
        query |= (db['trait'].id == arg)
    db(query).update(is_active=False)
    redirect(URL('index', vars=request.vars))

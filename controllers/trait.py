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
    import supert
    Supert = supert.Supert()

    trait_category = db.trait_category(request.vars.trait_category)
    if not trait_category:
        raise HTTP(400)

    query = (db.trait.is_active == True) & (db.trait.id_trait_category == trait_category.id)
    data = Supert.SUPERT(query, fields=['trait_option'])

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


def get_trait_by_category_and_option():
    """ vars: [category_name, trait_option] """

    cat_name = ''
    option = ''
    try:
        cat_name = request.vars.category_name
        option = request.vars.trait_option
    except:
        raise HTTP(404)
    if not cat_name and not option:
        raise HTTP(404)

    trait = db(
        (db.trait.id_trait_category == db.trait_category.id) &
        (db.trait_category.name == cat_name) &
        (db.trait.trait_option == option)
    ).select(db.trait.id).first()

    return dict(id=trait.id)


@auth.requires_membership('Items management')
def search():
    """ args: [category_name, term] """

    try:
        cat_name = request.vars.category_name
        term = request.vars.term

        match = db(
            (db.trait.id_trait_category == db.trait_category.id) &
            (db.trait_category.name == cat_name) &
            (db.trait.trait_option.contains(term))
        ).iterselect(
            db.trait.trait_option
        )
        match = [{'name': r.trait_option} for r in match]
        return dict(match=match)
    except:
        import traceback as tb
        tb.print_exc()
        raise HTTP(405)

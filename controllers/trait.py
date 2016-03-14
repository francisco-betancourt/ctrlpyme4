# -*- coding: utf-8 -*-
#
# Author: Daniel J. Ramirez

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

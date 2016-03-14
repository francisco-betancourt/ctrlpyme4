# -*- coding: utf-8 -*-
#
# Author: Daniel J. Ramirez



@auth.requires_membership('Items management')
def create():
    redirect_url = URL('index')
    parent = db.category(request.vars.parent)

    form = SQLFORM(db.category)

    if parent:
        redirect_url = URL('get', args=parent.id)
    form = SQLFORM(db.category, fields=['name', 'description', 'icon', 'trait_category1', 'trait_category2', 'trait_category3'])

    form.vars.parent = parent.id if parent else None

    if form.process().accepted:
        url_name = "%s%s" % (urlify_string(form.vars.name), form.vars.id)
        db.category(form.vars.id).update_record(url_name=url_name)
        response.flash = T("category created")
        redirect(redirect_url)
    elif form.errors:
        response.flash = T('form has errors')

    return dict(form=form, parent=parent)


@auth.requires_membership('Items management')
def get():
    category = db.category(request.args(0))
    if not category:
        redirect(URL('index'))
    query = db.category.parent == category.id
    data = super_table('category', ['name'], query, extra_options=category_extra_options)
    return locals()


@auth.requires_membership('Items management')
def update():
    category = db.category(request.args(0))
    if not category:
        raise HTTP(400)
    redirect_url = URL('index')
    parent = category.parent

    form = SQLFORM(db.category, category)

    if parent:
        redirect_url = URL('get', args=parent.id)
        form = SQLFORM(db.category, category, fields=['name', 'description', 'url_name', 'icon', 'trait_category1', 'trait_category2', 'trait_category3'])

    if form.process().accepted:
        url_name = "%s%s" % (urlify_string(form.vars.name), form.vars.id)
        db.category(form.vars.id).update_record(url_name=url_name)
        response.flash = T("category created")
        redirect(redirect_url)
    elif form.errors:
        response.flash = T('form has errors')

    return dict(form=form, category=category)


@auth.requires_membership('Items management')
def delete():
    return common_delete('category', request.args)


@auth.requires_membership('Items management')
def index():
    def category_options(row):
        update_btn, hide_btn = supert_default_options(row)
        return update_btn, hide_btn, OPTION_BTN('details', URL('index', args=row.id))
    query = db.category.parent == request.args(0)
    request.vars.orderby = 'name'
    data = SUPERT(query, fields=['name'], options_func=category_options)
    return locals()

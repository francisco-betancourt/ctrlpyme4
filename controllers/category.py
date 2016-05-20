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
    parent = db.category(request.vars.parent)
    redirect_url = URL('index')

    form = SQLFORM(db.category)

    if parent:
        redirect_url = URL('index', args=parent.id)
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
        redirect_url = URL('index', args=parent.id)
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
        return update_btn, hide_btn, OPTION_BTN('details', URL('index', args=row.id), title=T('subcategories'))
    query = db.category.parent == request.args(0)
    if not request.vars.show_hidden == 'yes':
        query &= db.category.is_active == True

    request.vars.orderby = 'name'
    data = SUPERT(query, fields=['name'], options_func=category_options)
    return locals()

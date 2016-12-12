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


@auth.requires_membership('Config')
def update_main():
    """ Updates the main configuration """

    settings = db(db.settings.id_store == None).select().first()
    if not settings:
        raise HTTP(404)

    form = SQLFORM(db.settings, settings, showid=False, submit_button=T('Save'))

    # this is used to list the top categories as page tags
    # cats = ', '.join([cat.name for cat in db(db.category.parent == None).select()])
    # form.vars.top_categories_string = cats

    if form.process().accepted:
        response.flash = T('form accepted')
        redirect(URL('update_main'))
    elif form.errors:
        response.flash = T('form has errors')
    return dict(form=form)

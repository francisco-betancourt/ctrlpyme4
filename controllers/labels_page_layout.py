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


@auth.requires(auth.has_membership('Config') or auth.has_membership('Safe config'))
def index():
    title = T('labels page layouts')
    data = SUPERT(db.labels_page_layout, fields=[
        'name', {
            'fields': ['label_cols', 'label_rows'],
            'label_as': T('Cols x Rows'),
            'custom_format': lambda row, fields: '%s x %s' % (row[fields[0]], row[fields[1]])
        }
    ])

    return locals()

@auth.requires(auth.has_membership('Config') or auth.has_membership('Safe config'))
def create():
    return common_create('labels_page_layout')


@auth.requires(auth.has_membership('Config') or auth.has_membership('Safe config'))
def update():
    return common_update('labels_page_layout', request.args)


@auth.requires(auth.has_membership('Config') or auth.has_membership('Safe config'))
def delete():
    return common_delete('labels_page_layout', request.args)

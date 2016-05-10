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
    title = T('paper sizes')
    data = SUPERT(db.paper_size, fields=[
        'name', 'width', 'height'
    ], options_enabled=False)

    return locals()


@auth.requires(auth.has_membership('Config') or auth.has_membership('Safe config'))
def create():
    form = SQLFORM(db.paper_size)

    if form.process().accepted:
        session.info = T("Paper size created")
        redirect(URL('index'))

    return locals()

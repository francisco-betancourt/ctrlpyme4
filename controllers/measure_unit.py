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


@auth.requires_membership('Config')
def create():
    """ """

    return common_create('measure_unit')


@auth.requires_membership('Config')
def get():
    pass


@auth.requires_membership('Config')
def update():
    """
    args: [measure_unit_id]
    """

    return common_update('measure_unit', request.args)


@auth.requires_membership('Config')
def delete():
    """
    args: [id_1, id_2, ..., id_n]
    """

    common_delete('measure_unit', request.args)


@auth.requires_membership('Config')
def index():
    data = common_index('measure_unit', ['name', 'symbol'])

    return locals()

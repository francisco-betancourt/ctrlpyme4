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

#
# This fragment of the db depends on some tables specified in db.py
#


# used calculate which items were purchased along other items, the higher the
# affinity the higher the amount of those items being sold toghether
db.define_table(
    'item_affinity'
    , Field('id_item1', 'reference item')
    , Field('id_item2', 'reference item')
    , Field('affinity', 'integer', default=0)
)
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

# help database definitions.

help_db.define_table(
    'the_help'
    , Field('lang')
    , Field('url_controller', default='')
    , Field('url_function', default='')
    , Field('title')
    , Field('description')
    , Field('tags', 'list:string')
    , Field('contents', 'text')

)
help_db.the_help.title.requires = IS_NOT_EMPTY(
    error_message='Please add a title'
)
help_db.the_help.description.requires = IS_NOT_EMPTY(
    error_message='Please add a description'
)
help_db.the_help.contents.requires = IS_NOT_EMPTY(
    error_message='Please add content'
)

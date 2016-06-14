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


def search():
    return locals()


def get():
    """ args: [help_id] """
    topic = db.the_help(request.args(0))
    if not topic:
        raise HTTP(404)

    return locals()


def index():
    """
        vars: [controller, function]
    """
    controller = request.vars.controller
    function = request.vars.function

    url_help = None
    if controller and function:
        url_help = db(
            (db.the_help.url_controller == controller)
            & (db.the_help.url_function == function)
        ).select()

    general_help = db(
        (db.the_help.url_controller == '')
        & (db.the_help.url_function == '')
    ).select()

    print general_help

    return locals()

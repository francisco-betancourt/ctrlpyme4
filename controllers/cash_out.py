# -*- coding: utf-8 -*-
#
# Copyright (C) <2016>  <Daniel J. Ramirez>
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

from datetime import timedelta

def create():
    """ args: [id_seller] """

    # cash
    last_cash_out = db( (db.cash_out.id_seller == request.args(0))
                      & (db.cash_out.is_done == True)
    ).select(orderby=db.cash_out.created_on).last()
    if last_cash_out:
        if request.now < last_cash_out.created_on + CASH_OUT_INTERVAL:
            print "not yet"
            redirect(URL('analytics', 'cash_out', vars=dict( id_cash_out=last_cash_out.id) ))

    seller = db.auth_user(request.args(0))
    if not seller:
        raise HTTP(404)
    if not auth.has_membership(None, seller.id, 'Sales checkout'):
        raise HTTP(405)
    new_cash_out_id = db.cash_out.insert(id_seller=seller.id)

    redirect(URL('analytics', 'cash_out', vars=dict( id_cash_out=new_cash_out_id) ))


def update():
    """ args: [id_cash_out]
        vars: [target <cash, notes>, value ]
    """
    if not request.vars.target in ['cash', 'notes']:
        raise HTTP(405)
    value = request.vars.value
    update_dict = {request.vars.target: request.vars.value}
    res = db((db.cash_out.id == request.args(0))
           & (db.cash_out.is_done == False)
    ).validate_and_update(**update_dict)
    if res.errors:
        raise HTTP(400)
    else:
        value = DQ(value, True) if request.vars.target == 'cash' else value
        return dict(target=request.vars.target, value=value)


def done():
    """ args: [id_cash_out] """

    value = request.vars.value
    cash_out = db.cash_out(request.args(0))
    if not cash_out:
        raise HTTP(404)
    cash_out.is_done = True
    cash_out.update_record()

    session.info = INFO(T('Cash out done'), T('Print report'), URL('analytics', 'cash_out', vars=dict(id_cash_out=cash_out.id, _print=True)), '_blank')

    redirect(URL('analytics', 'index'))

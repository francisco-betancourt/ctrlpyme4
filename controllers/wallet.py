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
# def get():
#     """
#         args: [wallet_id]
#     """
#
#     return dict(wallet=db.wallet(request.args(0)))
#
#
# def get_user_wallet():
#     """
#         args: [user_id]
#     """
#
#     user = db.auth_user(request.args(0))
#     print user
#     if not user:
#         raise HTTP(404)
#     return dict(wallet=db.wallet(user.id_wallet))
#
#
# def get_by_code():
#     """
#         args: [wallet_code]
#     """
#
#     return dict(wallet=db(db.wallet.wallet_code == request.args(0)).select().first())
#
#
# def print_wallet():
#     """
#         args: [wallet_id]
#     """
#
#     wallet = db.wallet(request.args(0))
#     if not wallet:
#         raise HTTP(404)
#
#     return locals()

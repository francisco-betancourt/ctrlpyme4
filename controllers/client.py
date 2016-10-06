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



@auth.requires_membership('Clients')
def profile():
    import supert
    Supert = supert.Supert()

    orders_data = Supert.SUPERT(db.sale_order.id_client == auth.user.id,
        fields=['id', 'is_ready'], searchable=False,
        options_func=lambda r: supert.OPTION_BTN('receipt', URL('ticket', 'get', vars=dict(id_bag=r.id_bag.id)), title=T('ticket') )
    )
    wallet_balance = 0
    if auth.user.id_wallet:
        wallet_balance = db.wallet(auth.user.id_wallet).balance
    wallet_balance = str(DQ(wallet_balance, True))
    return locals()


@auth.requires_membership('Clients management')
def update():
    client = db.auth_user(request.args(0))
    if not client or not client.is_client:
        raise HTTP(404)
    form = SQLFORM(db.auth_user, client)
    if form.process().accepted:
        response.flash = T('form accepted')
        redirect(URL('index'))
    elif form.errors:
        response.flash = T('form has errors')
    return dict(form=form)


@auth.requires_membership('Clients management')
def create():
    form = SQLFORM(db.auth_user)
    if form.process().accepted:
        clients_group = db(db.auth_group.role == 'Clients').select().first()
        new_client = db.auth_user(form.vars.id)
        new_client.is_client = True
        # add a new wallet to client
        new_client.id_wallet = db.wallet(new_wallet())
        new_client.update_record()
        if clients_group:
            db.auth_membership.insert(user_id=form.vars.id, group_id=clients_group.id)
        response.flash = T('Client created')
        redirect(URL('index'))
        # redirection()
    elif form.errors:
        response.flash = T('Error in form')
    return dict(form=form)


@auth.requires_membership('Clients management')
def ban():
    user = db.auth_user(request.args(0))
    if not user:
        raise HTTP(404)

    # ban client
    if auth.has_membership(user_id=user.id, role='Clients'):
        user.registration_key = 'blocked' if not user.registration_key else ''

    user.update_record()

    redirect(URL('index'))
    # redirection()


@auth.requires(auth.has_membership('Clients management'))
def index():
    """ List of clients """

    import supert
    Supert = supert.Supert()

    title = T('clients')
    def client_options(row):
        edit_btn = supert.OPTION_BTN(
            'edit', URL('update', args=row.id), title=T('edit')
        )
        icon_name = 'thumb_down'
        if row.registration_key == 'blocked':
            icon_name = 'thumb_up'
        ban_btn = supert.OPTION_BTN(
            icon_name, URL('ban', args=row.id), title=T('ban')
        )
        wallet_btn = supert.OPTION_BTN(
            'account_balance_wallet', 
            URL('wallet', 'index', args=row.id_wallet.id), title=T('wallet')
        )
        return edit_btn, ban_btn, wallet_btn

    query = (db.auth_user.is_client == True)
    data = Supert.SUPERT(
        query, [db.auth_user.ALL], fields=[
            'first_name', 'last_name', 'email',
            dict(
                fields=['phone_number'],
                custom_format=lambda r, f : A(r[f[0]], _href="tel:%s" % r[f[0]])
                , label_as=T('Phone number')
            ),
            dict(
                fields=['mobile_number'],
                custom_format=lambda r, f : A(r[f[0]], _href="tel:%s" % r[f[0]])
                , label_as=T('Mobile number')
            ),
            dict(
                fields=['id_wallet.balance'],
                custom_format=lambda r, f : '$ %s' % DQ(r[f[0]], True),
                label_as=T('Wallet balance')
            )
        ], options_func=client_options, selectable=False
    )
    return locals()

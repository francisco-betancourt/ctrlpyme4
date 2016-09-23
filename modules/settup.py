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


from gluon import current, URL


def create_payment_methods():
    db = current.db

    db.payment_opt.update_or_insert(db.payment_opt.name == 'wallet', name='wallet', allow_change=False, requires_account=False)
    db.payment_opt.update_or_insert(db.payment_opt.name == 'stripe', name='stripe', allow_change=False)

    db.commit()



def create_locale_setting():
    db = current.db
    T = current.T

    """ creates some locale default settings """
    db.measure_unit.update_or_insert(db.measure_unit.name == T('unit'), name=T('unit'), symbol='u')
    db.brand.update_or_insert(db.brand.name == T('no brand'), name=T('no brand'))
    db.payment_opt.update_or_insert(db.payment_opt.name == T('cash'), name=T('cash'), allow_change=True, requires_account=False)

    db.commit()



def create_groups():
    db = current.db
    auth = current.auth

    # create groups
    new_groups = {
          "Admin": "Allows company configuration, by itself it can not sell or perform any POS operations"
        , "Manager": "Accounts (Payable | Receivable), Analytics, Suppliers, Taxes"
        , "Inventories": "Create and apply inventories"
        , "Purchases": "Make Purchases"
        , "Items info": "Modify basic item information"
        , "Items management": "Modify brands, categories, hide and show items and create promotions, create items"
        , "Items prices": "Allows item price modification"

        , "Sales bags": "Bag creation and modification"
        , "Sales checkout": "Users in this group will be able to create a sale, register money income"
        , "Sales delivery": "Allows the modification of stocks and serial number capture for sold items"
        , "Sales invoices": "Invoice creation and cancellation, folios management"
        , "Sales returns": "Items returns, create credit notes"

        , "Clients": "Member of this group are clients"
        , "Page layout": "Menus, pages, colors, logo and visual configuration"
        , "VIP seller": "Allows price2 and price3 selection"
        , "Employee": "An Employee"
        , "Analytics": "Users in this group have acces to the analytic tools"
        , "Sale orders": "Solve client orders and notify clients about their orders"
        , "Stock transfers": "Create a stock transfer ticket, removing stock from the base store and reintegrating it in the receiving store"
        , "Offers": "Create offers that can contain discounts and free items"

        , 'Accounts payable': 'Settle payable accounts'
        , 'Accounts receivable': 'Settle receivable accounts'

        , 'Highlights': 'Create and edit highlighted things'

        , 'Config': 'App configuration'
        , 'Safe config': 'Non critical app configuration, like logo, page colors, ticket footer, cash out time interval '
        , 'Admin config': 'Critical configuration only for admin '
        , "Clients management": "Create, ban and unban clients"
        , 'Product loss': 'Create product losses'
        , 'Cash out': 'Create and view cash outs'
    }
    for key in new_groups.iterkeys():
        group = db(db.auth_group.role == key).select().first()
        if group:
            group.description = new_groups[key]
            group.update_record()
            continue
        auth.add_group(key, new_groups[key])

    db.commit()



def admin_roles():
    return [
          "Admin"
        , "Inventories"
        , "Purchases"
        , "Items info"
        , "Items management"
        , "Items prices"
        , "Sales bags"
        , "Sales checkout"
        , "Sales delivery"
        , "Sales invoices"
        , "Sales returns"
        , "Page layout"
        , "VIP seller"
        , "Employee"
        , "Analytics"
        , "Sale orders"
        , "Stock transfers"
        , "Offers"
        , 'Accounts payable'
        , 'Accounts receivable'
        , 'Highlights'
        , 'Config'
        , 'Safe config'
        , 'Admin config'
        , 'Product loss'
        , 'Cash out'
        , "Clients management"
    ]




def settup_admin_user(user_id):
    """ Transform a common user into an Admin """

    db = current.db
    auth = current.auth

    for role in admin_roles():
        group = db(db.auth_group.role == role).select().first()

        db.auth_membership.insert(
            user_id=user_id,
            group_id=group.id
        )



def create_admin_user(email):
    db = current.db
    auth = current.auth

    password = auth.random_password()
    print password

    admin = db.auth_user.validate_and_insert(
        first_name='Admin',
        last_name='user',
        email=email,
        password=password
    )

    for role in admin_roles():
        group = db(db.auth_group.role == role).select().first()

        db.auth_membership.insert(
            user_id=admin,
            group_id=group.id
        )

    mail = auth.settings.mailer

    mail.send(
        email,
        'Su punto de venta esta listo',
        'Su punto de venta esta listo para ser usado, ingrese a {app_url}, e inicie sesión con su correo {admin_email} y su contraseña: {password}'.format(
                app_url=URL('default', 'user/login'),
                admin_email=email, password=password
        )
    )

    db.commit()


def update_admins():
    db = current.db

    admin_group = db(db.auth_group.role == 'Admin').select().first()

    admins = db(
        (db.auth_membership.user_id == db.auth_user.id) &
        (db.auth_membership.group_id == admin_group.id)
    ).select(db.auth_user.id, distinct=db.auth_membership.user_id)

    # also consider the store groups
    admin_groups = db(
        (db.auth_group.role.belongs(admin_roles())) |
        (db.auth_group.role.like("Store %"))
    ).select()

    # maybe not the most efficient thing but this functions should not be used often
    for admin in admins:
        for group in admin_groups:
            membership = db(
                (db.auth_membership.user_id == admin.id) &
                (db.auth_membership.group_id == group.id)
            ).select().first()

            if not membership:
                db.auth_membership.insert(
                    user_id=admin,
                    group_id=group.id
                )
                print "Inserted membership %s" % group.role
    db.commit()



def settup_mx():
    db = current.db

    db.settings.update_or_insert(db.settings.id_store == None, id_store=None)

    # unidades de medida del SAT
    m_units = [
        ('Kilo', 'k'),
        ('Gramo', 'g'),
        ('Metro lineal', 'm'),
        ('Metro cuadrado', 'm2'),
        ('Metro cubico', 'm3'),
        ('Pieza', 'pz'),
        ('Cabeza', 'cabeza'),
        ('Litro', 'l'),
        ('Par', 'par'),
        ('Kilowatt', 'kw'),
        ('Millar', 'millar'),
        ('Juego', 'juego'),
        ('Kilowatt/hora', 'kw/h'),
        ('Tonelada', 'ton'),
        ('Barril', 'barril'),
        ('Gramo neto', 'g neto'),
        ('Decenas', 'decenas'),
        ('Cientos', 'cientos'),
        ('Docenas', 'docenas'),
        ('Caja', 'caja'),
        ('Botella', 'botella')
    ]
    for m_unit in m_units:
        db.measure_unit.update_or_insert(
            db.measure_unit.name == m_unit[0],
            name=m_unit[0], symbol=m_unit[1]
        )

    db.brand.update_or_insert(
        db.brand.name == 'Sin marca', name='Sin marca'
    )
    db.payment_opt.update_or_insert(
        db.payment_opt.name == 'Efectivo',
        name='Efectivo', allow_change=True, requires_account=False
    )

    db.commit()



def settup():
    db = current.db

    # create default settings
    db.settings.update_or_insert(db.settings.id_store == None, id_store=None)

    create_locale_setting()
    create_payment_methods()

    create_groups()

    db.commit()

    # create admin user
    # user_id = db.auth_user.validate_and_insert(
    #     first_name='Admin', last_name='Admin', password=auth.random_password(),
    # )
    # add Config, Admin, Analytics group

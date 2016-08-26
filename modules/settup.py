from gluon import current


def create_payment_methods():
    db = current.db

    db.payment_opt.update_or_insert(db.payment_opt.name == 'wallet', name='wallet', allow_change=False)
    db.payment_opt.update_or_insert(db.payment_opt.name == 'stripe', name='stripe', allow_change=False)


def create_locale_setting():
    db = current.db
    T = current.T

    """ creates some locale default settings """
    db.measure_unit.update_or_insert(db.measure_unit.name == T('unit'), name=T('unit'), symbol='u')
    db.brand.update_or_insert(db.brand.name == T('no brand'), name=T('no brand'))
    db.payment_opt.update_or_insert(db.payment_opt.name == T('cash'), name=T('cash'), allow_change=True)



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
        , "Items management": "Modify brands, categories, hide and show items and create promotions, item drops (lost or damaged items), create items"
        , "Items prices": "Allows item price modification"

        , "Sales bags": "Bag creation and modification"
        , "Sales checkout": "Users in this group will be able to create a sale, register money income"
        , "Sales delivery": "Allows the modification of stocks and serial number capture for sold items"
        , "Sales invoices": "Invoice creation and cancellation, folios management"
        , "Sales returns": "Items returns"

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

        , 'Highlights': 'Create an edit highlighted things'

        , 'Config': 'App configuration'
        , 'Safe config': 'Non critical app configuration '
        , 'Admin config': 'Critical configuration only for admin '
        , 'Product loss': 'Create product losses'
        , 'Cash out': 'Create cash outs'
    }
    for key in new_groups.iterkeys():
        if db(db.auth_group.role == key).select().first():
            continue
        auth.add_group(key, new_groups[key])


def create_admin_user(email, password):
    db = current.db

    admin_roles = [
          "Admin"
        # , "Inventories"
        # , "Purchases"
        , "Items info"
        , "Items management"
        , "Items prices"
        # , "Sales bags"
        # , "Sales checkout"
        # , "Sales delivery"
        # , "Sales invoices"
        # , "Sales returns"
        # , "Clients"
        , "Page layout"
        # , "VIP seller"
        # , "Employee"
        , "Analytics"
        # , "Sale orders"
        # , "Stock transfers"
        , "Offers"
        # , 'Accounts payable'
        # , 'Accounts receivable'
        , 'Highlights'
        , 'Config'
        , 'Safe config'
        , 'Admin config'
        # , 'Product loss'
        # , 'Cash out'
    ]

    admin = db.auth_user.validate_and_insert(
        first_name='Admin',
        last_name='user',
        email=email,
        password=password
    )

    for role in admin_roles:
        group = db(db.auth_group.role == role).select().first()

        db.auth_membership.insert(
            user_id=admin,
            group_id=group.id
        )


def settup():
    db = current.db

    # create default settings
    db.settings.update_or_insert(db.settings.id_store == None, id_store=None)

    create_locale_setting()
    create_payment_methods()
    create_payment_methods()

    create_groups()

    # create admin user
    # user_id = db.auth_user.validate_and_insert(
    #     first_name='Admin', last_name='Admin', password=auth.random_password(),
    # )
    # add Config, Admin, Analytics group

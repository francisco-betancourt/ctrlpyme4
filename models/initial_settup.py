#TODO move this to app creation
# only for development purposes



# create payment methods
db.payment_opt.update_or_insert(db.payment_opt.name == 'wallet', name='wallet', allow_change=False)
db.settings.update_or_insert(db.settings.id_store == None, id_store=None)
db.measure_unit.update_or_insert(db.measure_unit.name == 'unit', name='unit', symbol='u')
db.brand.update_or_insert(db.brand.name == 'no brand', name='no brand')
# db.payment_opt.update_or_insert(db.payment_opt.name == '', name='wallet', allow_change=False)
# db.payment_opt.update_or_insert(db.payment_opt.name == 'wallet', name='wallet', allow_change=False)



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
}


for key in new_groups.iterkeys():
    if db(db.auth_group.role == key).select().first():
        continue
    auth.add_group(key, new_groups[key])

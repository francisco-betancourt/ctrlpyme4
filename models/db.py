# -*- coding: utf-8 -*-

#########################################################################
## This scaffolding model makes your app work on google App Engine too
## File is released under public domain and you can use without limitations
#########################################################################

## if SSL/HTTPS is properly configured and you want all HTTP requests to
## be redirected to HTTPS, uncomment the line below:
# request.requires_https()

## app configuration made easy. Look inside private/appconfig.ini
from gluon.contrib.appconfig import AppConfig
## once in production, remove reload=True to gain full speed
myconf = AppConfig(reload=True)


if not request.env.web2py_runtime_gae:
    ## if NOT running on Google App Engine use SQLite or other DB
    ## For production add lazy_tables=True for a huge boost in performance
    db = DAL(myconf.take('db.uri'), pool_size=myconf.take('db.pool_size', cast=int), check_reserved=['all'],)
else:
    ## connect to Google BigTable (optional 'google:datastore://namespace')
    db = DAL('google:datastore+ndb')
    ## store sessions and tickets there
    session.connect(request, response, db=db)
    ## or store session in Memcache, Redis, etc.
    ## from gluon.contrib.memdb import MEMDB
    ## from google.appengine.api.memcache import Client
    ## session.connect(request, response, db = MEMDB(Client()))

## by default give a view/generic.extension to all actions from localhost
## none otherwise. a pattern can be 'controller/function.extension'
response.generic_patterns = ['*'] if request.is_local else []
## choose a style for forms
response.formstyle = myconf.take('forms.formstyle')  # or 'bootstrap3_stacked' or 'bootstrap2' or other
response.form_label_separator = myconf.take('forms.separator')


## (optional) optimize handling of static files
# response.optimize_css = 'concat,minify,inline'
# response.optimize_js = 'concat,minify,inline'
## (optional) static assets folder versioning
# response.static_version = '0.0.0'
#########################################################################
## Here is sample code if you need for
## - email capabilities
## - authentication (registration, login, logout, ... )
## - authorization (role based authorization)
## - services (xml, csv, json, xmlrpc, jsonrpc, amf, rss)
## - old style crud actions
## (more options discussed in gluon/tools.py)
#########################################################################

from gluon.tools import Auth, Service, PluginManager

auth = Auth(db)
service = Service()
plugins = PluginManager()

## create all tables needed by auth if not custom tables
auth.define_tables(username=False, signature=False)

## configure email
mail = auth.settings.mailer
mail.settings.server = 'logging' if request.is_local else myconf.take('smtp.sender')
mail.settings.sender = myconf.take('smtp.sender')
mail.settings.login = myconf.take('smtp.login')

## configure auth policy
auth.settings.registration_requires_verification = False
auth.settings.registration_requires_approval = False
auth.settings.reset_password_requires_verification = True

#########################################################################
## Define your tables below (or better in another model file) for example
##
## >>> db.define_table('mytable',Field('myfield','string'))
##
## Fields can be 'string','text','password','integer','double','boolean'
##       'date','time','datetime','blob','upload', 'reference TABLENAME'
## There is an implicit 'id integer autoincrement' field
## Consult manual for more options, validators, etc.
##
## More API examples for controllers:
##
## >>> db.mytable.insert(myfield='value')
## >>> rows=db(db.mytable.myfield=='value').select(db.mytable.ALL)
## >>> for row in rows: print row.id, row.myfield
#########################################################################

## after defining tables, uncomment below to enable auditing
# auth.enable_record_versioning(db)

""" database class object creation (initialization) """
db.define_table("brand",
    Field("name", "string", default=None),
    Field("logo", "upload", default=None),
    auth.signature)

db.define_table("trait_category",
    Field("name", "string", default=None),
    auth.signature)

db.define_table("measure_units",
    Field("name", "text", default=None),
    Field("symbol", "text", default=None),
    auth.signature)

db.define_table("tax",
    Field("name", "string", default=None),
    Field("percentage", "integer", default=None),
    Field("symbol", "string", default=None),
    auth.signature)


db.define_table(
    "company"
    , Field('name', 'string', default=None)
)


db.define_table("payment_opt",
    Field("name", "integer", default=None),
    Field("allow_change", "boolean", default=None),
    Field("credit_days", "integer", default=None),
    auth.signature)

db.define_table("address",
    Field("street", "string", default=None),
    Field("exterior", "string", default=None),
    Field("interior", "string", default=None),
    Field("neighborhood", "string", default=None),
    Field("city", "string", default=None),
    Field("municipality", "string", default=None),
    Field("state_province", "string", default=None),
    Field("country", "string", default=None),
    Field("reference", "string", default=None))

db.define_table("category",
    Field("name", "string", default=None),
    Field("description", "text", default=None),
    Field("url_name", "string", default=None),
    Field("icon", "upload", default=None),
    Field("parent", "reference category"),
    Field("trait_category1", "reference trait_category"),
    Field("trait_category2", "reference trait_category"),
    Field("trait_category3", "reference trait_category"),
    auth.signature)

db.define_table("trait",
    Field("id_trait_category", "reference trait_category"),
    Field("trait_option", "string", default=None),
    auth.signature)

db.define_table("item",
    Field("id_brand", "reference brand"),
    Field("categories", "list:reference category"),
    Field("name", "string", default=None),
    Field("description", "text", default=None),
    Field("upc", "string", length=12, default=None),
    Field("ean", "string", length=13, default=None),
    Field("sku", "string", length=20, default=None),
    Field("is_group", "boolean", default=False),
    Field("has_inventory", "boolean", default=True),
    Field("base_price", "decimal(16,6)", default=None),
    Field("price2", "decimal(16,6)", default=None),
    Field("price3", "decimal(16,6)", default=None),
    Field("id_trait1", "reference trait"),
    Field("trait1", "integer", default=None),
    Field("id_trait2", "reference trait"),
    Field("trait2", "integer", default=None),
    Field("id_trait3", "reference trait"),
    Field("trait3", "integer", default=None),
    Field("id_measure_units", "reference measure_units"),
    Field("taxes", "list:reference tax"),
    Field("url_name", "string", default=None),
    Field("extra_data1", "string", default=None),
    Field("is_extra1_public", "boolean", default=None),
    Field("extra_data2", "string", default=None),
    Field("is_extra2_public", "boolean", default=None),
    Field("extra_data3", "string", default=None),
    Field("is_extra3_public", "boolean", default=None),
    Field("allow_fractions", "boolean", default=None),
    Field("id_item_group", "reference item"),
    Field("thumb", "upload", default=None),
    Field("reward_points", "integer", default=None),
    auth.signature)

db.define_table("store",
    Field("id_company", "reference company"),
    Field("id_address", "reference address"),
    Field("name", "string", default=None),
    auth.signature)

db.define_table("store_config",
    Field("id_store", "reference store"),
    Field("param_name", "string", default=None),
    Field("param_value", "string", default=None),
    Field("param_type", "string", default=None),
    auth.signature)

db.define_table("supplier",
    Field("business_name", "string", default=None),
    Field("tax_id", "string", default=None),
    Field("id_address", "reference address"),
    auth.signature)

db.define_table("purchase",
    Field("id_payment_opt", "reference payment_opt"),
    Field("id_supplier", "reference supplier"),
    Field("id_store", "reference store"),
    Field("invoice_number", "integer", default=None),
    Field("subtotal", "integer", default=None),
    Field("total", "decimal(16,6)", default=None),
    Field("shipping_cost", "decimal(16,6)", default=None),
    Field("tracking_number", "integer", default=None),
    Field("purchase_xml", "text", default=None),
    auth.signature)

db.define_table("purchase_item",
    Field("id_purchase", "reference purchase"),
    Field("id_item", "reference item"),
    Field("quantity", "decimal(16,6)", default=None),
    Field("price", "decimal(16,6)", default=None),
    Field("taxes", "integer", default=None),
    Field("serial_numbers", "text", default=None))

db.define_table("stock",
    Field("id_store", "reference store"),
    Field("id_purchase", "reference purchase"),
    Field("id_item", "reference item"),
    Field("quantity", "integer", default=None),
    auth.signature)

db.define_table("bag",
    Field("id_store", "reference store"),
    Field("completed", "string", default=None),
    auth.signature)

db.define_table("bag_items",
    Field("id_item", "reference item"),
    Field("id_bag", "reference bag"),
    Field("quantity", "decimal(16,6)", default=None),
    Field("buy_price", "decimal(16,6)", default=None),
    Field("buy_date", "datetime", default=None),
    Field("sale_price", "decimal(16,6)", default=None),
    Field("sale_taxes", "decimal(16,6)", default=None),
    Field("product_name", "string", default=None),
    Field("sale_code", "string", default=None),
    Field("serial_number", "string", default=None))

db.define_table("sale",
    Field("id_bag", "reference bag"),
    Field("consecutive", "integer", default=None),
    Field("subtotal", "decimal(16,6)", default=None),
    Field("total", "integer", default=None),
    Field("quantity", "integer", default=None),
    Field("client", "integer", default=None),
    Field("reward_points", "integer", default=None),
    Field("is_invoiced", "boolean", default=None),
    Field("id_store", "reference store"),
    auth.signature)

db.define_table("sale_log",
    Field("id_sale", "reference sale"),
    Field("sale_event", "string", default=None),
    Field("event_date", "datetime", default=None),
    auth.signature)

db.define_table("credit_note",
    Field("id_sale", "reference sale"),
    Field("subtotal", "decimal(16,6)", default=None),
    Field("total", "decimal(16,6)", default=None),
    Field("is_usable", "boolean", default=None),
    Field("code", "string", default=None),
    auth.signature)

db.define_table("credit_note_item",
    Field("id_credit_note", "reference credit_note"),
    Field("id_bag_items", "reference bag_items"),
    Field("quantity", "decimal(16,6)", default=None))

db.define_table("inventory",
    Field("id_store", "reference store"),
    Field("is_partital", "boolean", default=None),
    Field("done", "boolean", default=None),
    auth.signature)

db.define_table("inventory_items",
    Field("id_inventory", "reference inventory"),
    Field("id_item", "reference item"),
    Field("system_qty", "integer", default=None),
    Field("physical_qty", "integer", default=None))

db.define_table("payment",
    Field("id_payment_opt", "reference payment_opt"),
    Field("id_sale", "reference sale"),
    Field("amount", "decimal(16,6)", default=None),
    Field("account", "string", default=None),
    Field("change_amount", "decimal(16,6)", default=None),
    auth.signature)

db.define_table("item_images",
    Field("id_item", "reference item"),
    Field("image", "upload", default=None),
    Field("thumb", "upload", default=None))

db.define_table("promotion",
    Field("id_store", "reference store"),
    Field("json_data", "text", default=None),
    Field("code", "string", default=None),
    Field("starts_on", "datetime", default=None),
    Field("ends_on", "datetime", default=None),
    Field("is_coupon", "boolean", default=None),
    Field("is_combinable", "boolean", default=None),
    auth.signature)

db.define_table("account_receivable",
    Field("id_sale", "reference sale"),
    Field("is_settled", "boolean", default=None),
    auth.signature)

db.define_table("account_payable",
    Field("id_purchase", "reference purchase"),
    Field("is_settled", "boolean", default=None),
    auth.signature)

db.define_table("tax_data",
    Field("tax_id", "integer", default=None),
    Field("business_name", "string", default=None),
    Field("id_address", "reference address"),
    auth.signature)

db.define_table("invoice",
    Field("id_sale", "reference sale"),
    Field("id_tax_data", "reference tax_data"),
    Field("invoice_xml", "text", default=None),
    Field("uuid", "string", default=None),
    Field("sat_seal", "string", default=None),
    Field("certification_date", "datetime", default=None),
    Field("folio", "integer", default=None),
    Field("is_cancelled", "boolean", default=None),
    Field("cancel_date", "datetime", default=None),
    Field("acknowledgement", "text", default=None),
    auth.signature)

""" Relations between tables (remove fields you don't need from requires) """
db.item.id_brand.requires=IS_IN_DB( db, 'brand.id', ' %(name)s %(logo)s')
db.item.id_trait1.requires=IS_IN_DB( db, 'trait.id', ' %(id_trait_category)s %(option)s')
db.item.id_trait2.requires=IS_IN_DB( db, 'trait.id', ' %(id_trait_category)s %(option)s')
db.item.id_trait3.requires=IS_IN_DB( db, 'trait.id', ' %(id_trait_category)s %(option)s')
db.item.id_measure_units.requires=IS_IN_DB( db, 'measure_units.id', ' %(name)s %(symbol)s')
db.category.parent.requires=IS_IN_DB( db, 'category.id', ' %(name)s %(description)s %(url_name)s %(icon)s %(parent)s %(trait_category1)s %(trait_category2)s %(trait_category3)s')
db.category.trait_category1.requires=IS_IN_DB( db, 'trait_category.id', ' %(name)s')
db.category.trait_category2.requires=IS_IN_DB( db, 'trait_category.id', ' %(name)s')
db.category.trait_category3.requires=IS_IN_DB( db, 'trait_category.id', ' %(name)s')
db.trait.id_trait_category.requires=IS_IN_DB( db, 'trait_category.id', ' %(name)s')
db.store.id_company.requires=IS_IN_DB( db, 'company.id', '')
db.store.id_address.requires=IS_IN_DB( db, 'address.id', ' %(street)s %(exterior)s %(interior)s %(neighborhood)s %(city)s %(municipality)s %(state_province)s %(country)s %(reference)s')
db.store_config.id_store.requires=IS_IN_DB( db, 'store.id', ' %(id_company)s %(id_address)s %(name)s')
db.purchase.id_payment_opt.requires=IS_IN_DB( db, 'payment_opt.id', ' %(name)s %(allow_change)s %(credit_days)s')
db.purchase.id_supplier.requires=IS_IN_DB( db, 'supplier.id', ' %(business_name)s %(tax_id)s %(id_address)s')
db.purchase.id_store.requires=IS_IN_DB( db, 'store.id', ' %(id_company)s %(id_address)s %(name)s')
db.supplier.id_address.requires=IS_IN_DB( db, 'address.id', ' %(street)s %(exterior)s %(interior)s %(neighborhood)s %(city)s %(municipality)s %(state_province)s %(country)s %(reference)s')
db.purchase_item.id_purchase.requires=IS_IN_DB( db, 'purchase.id', ' %(id_payment_opt)s %(id_supplier)s %(id_store)s %(invoice_number)s %(subtotal)s %(total)s %(shipping_cost)s %(tracking_number)s %(xml)s')
db.stock.id_store.requires=IS_IN_DB( db, 'store.id', ' %(id_company)s %(id_address)s %(name)s')
db.stock.id_purchase.requires=IS_IN_DB( db, 'purchase.id', ' %(id_payment_opt)s %(id_supplier)s %(id_store)s %(invoice_number)s %(subtotal)s %(total)s %(shipping_cost)s %(tracking_number)s %(xml)s')
db.bag.id_store.requires=IS_IN_DB( db, 'store.id', ' %(id_company)s %(id_address)s %(name)s')
db.bag_items.id_bag.requires=IS_IN_DB( db, 'bag.id', ' %(id_store)s %(completed)s')
db.sale.id_bag.requires=IS_IN_DB( db, 'bag.id', ' %(id_store)s %(completed)s')
db.sale.id_store.requires=IS_IN_DB( db, 'store.id', ' %(id_company)s %(id_address)s %(name)s')
db.sale_log.id_sale.requires=IS_IN_DB( db, 'sale.id', ' %(id_bag)s %(number)s %(subtotal)s %(total)s %(quantity)s %(client)s %(reward_points)s %(is_invoiced)s %(id_store)s')
db.credit_note.id_sale.requires=IS_IN_DB( db, 'sale.id', ' %(id_bag)s %(number)s %(subtotal)s %(total)s %(quantity)s %(client)s %(reward_points)s %(is_invoiced)s %(id_store)s')
db.credit_note_item.id_credit_note.requires=IS_IN_DB( db, 'credit_note.id', ' %(id_sale)s %(subtotal)s %(total)s %(is_usable)s %(code)s')
db.credit_note_item.id_bag_items.requires=IS_IN_DB( db, 'bag_items.id', ' %(id_item)s %(id_bag)s %(quantity)s %(buy_price)s %(buy_date)s %(sale_price)s %(sale_taxes)s %(product_name)s %(sale_code)s %(serial_number)s')
db.inventory.id_store.requires=IS_IN_DB( db, 'store.id', ' %(id_company)s %(id_address)s %(name)s')
db.inventory_items.id_inventory.requires=IS_IN_DB( db, 'inventory.id', ' %(id_store)s %(is_partital)s %(done)s')
db.payment.id_payment_opt.requires=IS_IN_DB( db, 'payment_opt.id', ' %(name)s %(allow_change)s %(credit_days)s')
db.payment.id_sale.requires=IS_IN_DB( db, 'sale.id', ' %(id_bag)s %(number)s %(subtotal)s %(total)s %(quantity)s %(client)s %(reward_points)s %(is_invoiced)s %(id_store)s')
db.promotion.id_store.requires=IS_IN_DB( db, 'store.id', ' %(id_company)s %(id_address)s %(name)s')
db.account_receivable.id_sale.requires=IS_IN_DB( db, 'sale.id', ' %(id_bag)s %(number)s %(subtotal)s %(total)s %(quantity)s %(client)s %(reward_points)s %(is_invoiced)s %(id_store)s')
db.account_payable.id_purchase.requires=IS_IN_DB( db, 'purchase.id', ' %(id_payment_opt)s %(id_supplier)s %(id_store)s %(invoice_number)s %(subtotal)s %(total)s %(shipping_cost)s %(tracking_number)s %(xml)s')
db.invoice.id_sale.requires=IS_IN_DB( db, 'sale.id', ' %(id_bag)s %(number)s %(subtotal)s %(total)s %(quantity)s %(client)s %(reward_points)s %(is_invoiced)s %(id_store)s')
db.invoice.id_tax_data.requires=IS_IN_DB( db, 'tax_data.id', ' %(tax_id)s %(business_name)s %(id_address)s')
db.tax_data.id_address.requires=IS_IN_DB( db, 'address.id', ' %(street)s %(exterior)s %(interior)s %(neighborhood)s %(city)s %(municipality)s %(state_province)s %(country)s %(reference)s')

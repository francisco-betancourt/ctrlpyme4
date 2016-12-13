# -*- coding: utf-8 -*-

#########################################################################
## This scaffolding model makes your app work on google App Engine too
## File is released under public domain and you can use without limitations
#########################################################################

## if SSL/HTTPS is properly configured and you want all HTTP requests to
## be redirected to HTTPS, uncomment the line below:
# request.requires_https()

## app configuration made easy. Look inside private/appconfig.ini
# from gluon.contrib.appconfig import AppConfig
## once in production, remove reload=True to gain full speed
# CONF = AppConfig(reload=True)

# from gluon.custom_import import track_changes; track_changes(True)
from constants import CONF, BAG_ACTIVE

import os

if not request.env.web2py_runtime_gae:
    ## if NOT running on Google App Engine use SQLite or other DB
    ## For production add lazy_tables=True for a huge boost in performance
    migrate = CONF.take('db.migrate', cast=int) == 1
    lazy_tables = CONF.take('db.lazy_tables', cast=int) == 1
    db = DAL(
        CONF.take('db.uri'),
        pool_size=CONF.take('db.pool_size', cast=int),
        check_reserved=['all'],
        migrate=migrate,
        migrate_enabled=migrate,
        lazy_tables=lazy_tables
    )
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
# response.generic_patterns = ['*']
## choose a style for forms
response.formstyle = CONF.take('forms.formstyle')  # or 'bootstrap3_stacked' or 'bootstrap2' or other
response.form_label_separator = CONF.take('forms.separator')


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


# set current db and auth
from gluon import current
current.db = db
current.auth = auth


db.define_table(
  'wallet'
  , Field('wallet_code', notnull=True, label=T('Wallet code'), writable=False, readable=False)
  , Field('balance', 'decimal(16,6)', default=0, label=T('Balance'), writable=False, readable=False)
)

auth.settings.extra_fields['auth_user'] = [
        Field('access_code', default="000000", label=T('Access code'), readable=False, writable=False)
      , Field('id_wallet', 'reference wallet', label=T('Wallet'), readable=False, writable=False)
      , Field('access_card_index', 'integer', readable=False, writable=False,
              default=0
        )
      , Field('is_client', 'boolean', default=False, readable=False, writable=False)
      , Field('stripe_customer_id', default=None, readable=False, writable=False)
      , Field('max_discount', "decimal(16,6)", default=0, readable=False, writable=False)
      , Field('phone_number', 'string', default='', label=T('Phone number'))
      , Field('mobile_number', 'string', default='', label=T('Mobile number'))
]

## create all tables needed by auth if not custom tables
auth.define_tables(username=False, signature=False)

## configure email
mail = auth.settings.mailer
mail.settings.server = CONF.take('smtp.server')
mail.settings.sender = CONF.take('smtp.sender')
mail.settings.login = CONF.take('smtp.login')

## configure auth policy
auth.settings.registration_requires_verification = True
auth.settings.registration_requires_approval = False
auth.settings.reset_password_requires_verification = True
auth.settings.login_next = URL('user', 'post_login', vars=request.vars)
auth.settings.logout_next = URL('user', 'post_logout')

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


from custom_validators import *


not_empty_requires = IS_NOT_EMPTY(error_message='cannot be empty!')


""" database class object creation (initialization) """


EARNING_VALIDATOR = IS_DECIMAL_IN_RANGE(0, error_message="")

db.define_table("brand",
    Field("name", "string", default="", label=T('Name')),
    Field("logo", "upload", default="", label=T('Logo'), uploadfolder=os.path.join(request.folder, 'static/uploads')),
    Field(
        "earnp_base", "decimal(16,6)", default=0,
        label=T("Earning percentage base")
    ),
    Field(
        "earnp_2", "decimal(16,6)", default=0,
        label=T("Earning percentage 2")
    ),
    Field(
        "earnp_3", "decimal(16,6)", default=0,
        label=T("Earning percentage 3")
    ),
    auth.signature)
db.brand.name.requires = not_empty_requires
db.brand.earnp_base.requires = EARNING_VALIDATOR
db.brand.earnp_2.requires = EARNING_VALIDATOR
db.brand.earnp_3.requires = EARNING_VALIDATOR


db.define_table("trait_category",
    Field("name", "string", default="", label=T('Name')),
    auth.signature)
db.trait_category.name.requires = not_empty_requires


db.define_table("measure_unit",
    Field("name", "string", default="", label=T('Name')),
    Field("symbol", "string", default="", label=T('Symbol')),
    auth.signature)
db.measure_unit.name.requires = not_empty_requires


db.define_table("tax",
    Field("name", "string", default="", label=T('Name')),
    Field("percentage", "integer", default=1, label=T('Percentage')),
    Field("symbol", "string", default="", label=T('Symbol')),
    Field("tax_type", "integer", default=1, label=T('Tax Type')),
    auth.signature,
    format='%(name)s')
db.tax.name.requires = not_empty_requires
db.tax.percentage.requires = IS_INT_IN_RANGE(1, 99)
db.tax.symbol.requires = [not_empty_requires, IS_LENGTH(1)]



# probabily deprecated
db.define_table(
    "company"
    , Field('name', 'string', default=None, label=T('Name'))
)
db.company.name.requires = not_empty_requires


payment_opt_format = '%(name)s'
db.define_table("payment_opt",
    Field("name", "string", default=None, label=T('Name')),
    Field("allow_change", "boolean", default=False, label=T('Allow change')),
    Field("requires_account", "boolean", default=True, label=T('Requires account')),
    Field("credit_days", "integer", default=None, label=T('Credit days')),
    auth.signature, format=payment_opt_format
    )
db.payment_opt.name.requires = [
    not_empty_requires, IS_NOT_IN_DB(db, 'payment_opt.name')
]


address_format = '%(street)s %(exterior)s %(interior)s %(neighborhood)s %(city)s %(municipality)s %(state_province)s %(country)s %(reference)s'
db.define_table("address",
    Field("street", "string", default=None, label=T('Street')),
    Field("exterior", "string", default=None, label=T('Exterior number')),
    Field("interior", "string", default=None, label=T('Interior number')),
    Field("neighborhood", "string", default=None, label=T('Neighborhood')),
    Field("city", "string", default=None, label=T('City')),
    Field("municipality", "string", default=None, label=T('Municipality')),
    Field("state_province", "string", default=None, label=T('State or Province')),
    Field("postal_code", "string", default=None, label=T('Postal code')),
    Field("country", "string", default=None, label=T('Country')),
    Field("reference", "string", default=None, label=T('Address Reference')),
    auth.signature, format=address_format
    )


store_format = '%(name)s'
db.define_table("store",
    Field("id_address", "reference address", label=T('Address')),
    Field("name", "string", default=None, label=T('Name')),
    Field("consecutive", "integer", default=1, readable=False, writable=False),
    Field('map_url', default=None, label=T('Map url')),

    Field('phone_number_1', default='', label=T('Phone number')),
    Field('phone_number_2', default='', label=T('Phone number')),
    Field('email', default='', label=T('Email')),

    Field("image", "upload", default=None, label=T('Image'), uploadfolder=os.path.join(request.folder, 'static/uploads')),

    #Fields required for CFDI Invoice
    Field('certificate',type='upload',autodelete=True,readable=False,writable=False,
		uploadfolder=request.folder+'/private/',label=T("Certificate")+"(.cer)"),
	Field('private_key',type='upload',autodelete=True,readable=False,writable=False,
		uploadfolder=request.folder+'/private/',label=T("Private Key")+"(.key)"),
	Field('invoice_series', label=T("CFDI Series"),readable=False),
	#Completamente ocultos se generan cuando actualizas certificado
	Field('certificate_number',readable=False,writable=False),
	Field('certificate_base64',type="text",readable=False,writable=False),
	Field('csdpass',type="password",readable=False,writable=False),
    auth.signature, format=store_format
    )
db.store.id_address.requires=IS_IN_DB( db, 'address.id', address_format)
db.store.name.requires = not_empty_requires
db.store.email.requires = IS_EMPTY_OR(IS_EMAIL())


highlight_image_validator = IS_IMAGE(extensions=('jpeg', 'png'), maxsize=(1000, 1000))


# DEPRECATED
db.define_table(
    'notification'
    , Field('id_store', 'reference store', label=T('Store'))
    # , Field('id_group', 'reference auth_group', label=T('Group'))
    , Field('title', label=T('Title'))
    , Field('description', label=T('Description'))
    , Field('url', label=T('URL'))
    , Field('is_done', 'boolean', default=False, label=T('Is done'))
    , auth.signature
)
db.notification.id_store.requires = IS_EMPTY_OR(IS_IN_DB(db(db.store.is_active == True), 'store.id', '%(name)s'))
db.notification.url.requires = IS_URL()



db.define_table(
     'wallet_transaction'
    , Field('id_wallet', 'reference wallet', notnull=True)
    , Field('amount', 'decimal(16,6)', default=0, label=T('Amount'))
    , Field('concept', 'integer', notnull=True, label=T('Concept'))
    , Field('is_system_op', 'boolean', default=False)
    , Field('ref_id', 'integer')
    , auth.signature
)



db.define_table(
    'highlight'
    , Field('id_store', 'reference store', label=T('Store'))
    , Field('title', label=T('Title'))
    , Field('description', label=T('Description'))
    , Field('url', label=T('URL'))
    , Field('bg_image', 'upload', label=T('Image'), uploadfolder=os.path.join(request.folder, 'static/uploads'))
    , auth.signature
)
db.highlight.id_store.requires = IS_EMPTY_OR(IS_IN_DB(db(db.store.is_active == True), 'store.id', store_format))
db.highlight.url.requires = IS_URL()
db.highlight.bg_image.requires = highlight_image_validator
db.highlight.title.requires = not_empty_requires


db.define_table(
  'settings'
  , Field('id_store', 'reference store', default=None, readable=False, writable=False)
  , Field('company_name', label=T('Name'))
  , Field('company_slogan', label=T('Slogan'))
  , Field('company_logo', 'upload', label=T('Logo'), default=None, uploadfolder=os.path.join(request.folder, 'static/uploads'))

  , Field('extra_field_1', label=T('Extra field') + '1')
  , Field('extra_field_2', label=T('Extra field') + '2')
  , Field('extra_field_3', label=T('Extra field') + '3')

  # true if the store only allows whitelisted clients
  , Field('clients_whitelist', 'boolean', label=T('Use clients whitelist'), default=True, readable=False, writable=False)

  , Field('ticket_footer', 'text', label=T('Ticket footer'))

  , Field('primary_color', label=T('Primary color'))
  , Field('primary_color_text', label=T('Primary color text'))
  , Field('accent_color', label=T('Accent color'))
  , Field('accent_color_text', label=T('Accent color text'))
  , Field('base_color', label=T('Base color'))
  , Field('base_color_text', label=T('Base color text'))
  , Field('top_categories_string', readable=False, writable=False)

  # 1 day default cash out interval
  , Field('cash_out_interval_days', 'integer', default=1, label=T('Cash out interval days'))

  , Field(
        'merge_credit_notes_in_sale', 'boolean', default=False,
        label=T('Show credit notes in sale ticket')
    )


  # some chached data
  # the mount of time in minutes that the cached data will be available
  , Field('cached_data_timeout', 'integer', default=120, readable=False, writable=False)
  , Field('cached_popular_items', readable=False, writable=False)

  , auth.signature
)
hex_match = IS_MATCH('#[0-9a-fA-F]{6}', error_message=T('not hex'))
db.settings.primary_color.requires = IS_EMPTY_OR(hex_match)
db.settings.primary_color_text.requires = IS_EMPTY_OR(hex_match)
db.settings.accent_color.requires = IS_EMPTY_OR(hex_match)
db.settings.accent_color_text.requires = IS_EMPTY_OR(hex_match)
db.settings.base_color.requires = IS_EMPTY_OR(hex_match)
db.settings.base_color_text.requires = IS_EMPTY_OR(hex_match)
db.settings.id_store.requires = IS_EMPTY_OR(IS_IN_DB(db, 'store.id'))
db.settings.extra_field_1.requires = IS_EMPTY_OR(IS_LENGTH(50))
db.settings.extra_field_2.requires = IS_EMPTY_OR(IS_LENGTH(50))
db.settings.extra_field_3.requires = IS_EMPTY_OR(IS_LENGTH(50))


db.define_table(
    'cached_data'
    , Field('name', 'integer', readable=False, writable=False)
    , Field('val', readable=False, writable=False)
    , auth.signature
)


db.define_table(
    'paper_size'
    , Field('name', label=T('Name'), unique=True)
    # in centimeters
    , Field('width', 'decimal(16,6)', label=T('Paper width (cm)'))
    , Field('height', 'decimal(16,6)', label=T('Paper height (cm)'))
)
db.paper_size.name.requires = not_empty_requires
db.paper_size.width.requires = IS_DECIMAL_IN_RANGE(1, 100, dot='.')
db.paper_size.height.requires = IS_DECIMAL_IN_RANGE(1, 100, dot='.')


db.define_table(
    'labels_page_layout'
    , Field('name', label=T('Name'))
    , Field('id_paper_size', 'reference paper_size', label=T("Paper size"))
    , Field('margin_top', 'decimal(16,6)', default=1, label=T('Paper margin top') + ' (cm)')
    , Field('margin_right', 'decimal(16,6)', default=1, label=T('Paper margin right') + ' (cm)')
    , Field('margin_bottom', 'decimal(16,6)', default=1, label=T('Paper margin bottom') + ' (cm)')
    , Field('margin_left', 'decimal(16,6)', default=1, label=T('Paper margin left') + ' (cm)')

    , Field(
        'space_x', 'decimal(16,6)', default=.5,
        label=T('Labels') + ': ' + T('left spacing') + ' (cm)'
    )
    , Field(
        'space_y', 'decimal(16,6)', default=.5,
        label=T('Labels') + ': ' + T('bottom spacing') + ' (cm)'
    )
    , Field('label_cols', 'integer', default=1, label=T('Labels columns'))
    , Field('label_rows', 'integer', default=1, label=T('Labels rows'))
    , Field(
        'show_name', 'boolean', default=True,
        label=T('Label') + ':' + T('Show name')
    )
    , Field(
        'show_price', 'boolean', default=True,
        label=T('Label') + ':' + T('Show price')
    )
)
db.labels_page_layout.name.requires = not_empty_requires
db.labels_page_layout.margin_top.requires = IS_DECIMAL_IN_RANGE(1, 10, dot='.')
db.labels_page_layout.margin_right.requires = IS_DECIMAL_IN_RANGE(1, 10, dot='.')
db.labels_page_layout.margin_bottom.requires = IS_DECIMAL_IN_RANGE(1, 10, dot='.')
db.labels_page_layout.margin_left.requires = IS_DECIMAL_IN_RANGE(1, 10, dot='.')
db.labels_page_layout.id_paper_size.requires = IS_IN_DB(db, db.paper_size.id, '%(name)s')
db.labels_page_layout.label_cols.requires = IS_INT_IN_RANGE(1, 20)
db.labels_page_layout.label_rows.requires = IS_INT_IN_RANGE(1, 20)
db.labels_page_layout.space_x.requires = IS_DECIMAL_IN_RANGE(0, 2)
db.labels_page_layout.space_y.requires = IS_DECIMAL_IN_RANGE(0, 2)


db.define_table("category",
    Field("name", "string", default=None, label=T('Name')),
    Field("description", "text", default=None, label=T('Description')),
    Field("url_name", "string", default=None, label=T('URL Name'), readable=False, writable=False),
    Field("icon", "upload", default=None, label=T('Icon'), uploadfolder=os.path.join(request.folder, 'static/uploads')),
    Field("parent", "reference category", label=T('Parent category'), readable=False, writable=False),
    auth.signature)
db.category.name.requires = not_empty_requires
db.category.parent.requires=IS_EMPTY_OR(IS_IN_DB(db(db.category.is_active == True), 'category.id', ' %(name)s %(description)s %(url_name)s %(icon)s %(parent)s'))


db.define_table("trait",
    Field("id_trait_category", "reference trait_category", label=T('Trait category')),
    Field("trait_option", "string", default=None, label=T('Option')),
    auth.signature)
db.trait.trait_option.requires = not_empty_requires



db.define_table("item",
    Field("id_brand", "reference brand", label=T('Brand')),
    Field("categories", "list:reference category", default=[], label=T('Categories')),
    Field("traits", "list:reference trait", label=T("Traits"), readable=False, writable=False),
    Field("name", "string", default='', label=T('Name')),
    Field("description", "text", default='', label=T('Description')),
    Field("upc", "string", length=12, default=None, label=T('UPC')),
    Field("ean", "string", length=13, default=None, label=T('EAN')),
    Field("sku", "string", length=40, default=None, label=T('SKU')),
    Field("is_bundle", "boolean", default=False, label=T('Is bundle'), readable=False, writable=False),
    Field("has_inventory", "boolean", default=True, label=T('Has inventory')),

    Field("base_price", "decimal(16,6)", default=1, label=T('Base price')),
    Field("price2", "decimal(16,6)", default=None, label=T('Price')+" 2"),
    Field("price3", "decimal(16,6)", default=None, label=T('Price')+" 3"),

    # last earning percentage reported, used to calculate the sale prices based on purchase price
    Field(
        "earnp_base", "decimal(16,6)", default=0,
        label=T("Earning percentage base")
    ),
    Field(
        "earnp_2", "decimal(16,6)", default=0,
        label=T("Earning percentage 2")
    ),
    Field(
        "earnp_3", "decimal(16,6)", default=0,
        label=T("Earning percentage 3")
    ),

    Field("id_measure_unit", "reference measure_unit", label=T('Measure unit')),
    Field("taxes", "list:reference tax", label=T('Taxes')),
    Field("url_name", "string", default='', label=T('URL Name'), readable=False, writable=False),
    Field("extra_data1", "string", default=None, label=T('Extra Data')+" 1"),
    Field("extra_data2", "string", default=None, label=T('Extra Data')+" 2"),
    Field("extra_data3", "string", default=None, label=T('Extra Data')+" 3"),
    Field("allow_fractions", "boolean", default=None, label=T('Allow fractions')),
    Field("reward_points", "decimal(16,6)", default=0, label=T('Reward Points')),
    Field("is_returnable", "boolean", default=True, label=T('Is returnable')),
    Field("has_serial_number", "boolean", default=False, label=T('Has serial number')),
    auth.signature
)
db.item.name.requires = not_empty_requires
db.item.id_brand.requires=IS_IN_DB(
    db(db.brand.is_active == True), 'brand.id', ' %(name)s'
)
db.item.id_measure_unit.requires=IS_IN_DB(
    db(db.measure_unit.is_active == True), 'measure_unit.id', ' %(name)s %(symbol)s'
)
db.item.taxes.requires=IS_EMPTY_OR(
    IS_IN_DB(db(db.tax.is_active == True), 'tax.id', ' %(name)s', multiple=True)
)

BC_MATCH = IS_MATCH(
    '^[0-9a-zA-Z-$.%*/]+$',
    error_message=T('Only alphanumeric characters, -, $, ., %, *, /')
)
db.item.sku.requires=[IS_BARCODE_AVAILABLE(db, request.vars.sku), BC_MATCH]
db.item.ean.requires=[
    IS_EMPTY_OR(IS_LENGTH(13, 5)),
    IS_BARCODE_AVAILABLE(db, request.vars.ean),
    IS_EMPTY_OR(BC_MATCH),
]
db.item.upc.requires=[
    IS_EMPTY_OR(IS_LENGTH(12, 6)),
    IS_BARCODE_AVAILABLE(db, request.vars.upc),
    IS_EMPTY_OR(BC_MATCH),
]

PRICE_RANGE_VALIDATOR = IS_DECIMAL_IN_RANGE(
    .00001, 10000000, dot=".", error_message=T('Price needs to be more than 0')
)
db.item.base_price.requires = PRICE_RANGE_VALIDATOR
db.item.price2.requires = IS_EMPTY_OR(PRICE_RANGE_VALIDATOR)
db.item.price3.requires = IS_EMPTY_OR(PRICE_RANGE_VALIDATOR)
db.item.reward_points.requires = IS_DECIMAL_IN_RANGE(0, 100000)



db.define_table(
  'bundle_item'
  , Field('id_bundle', 'reference item')
  , Field('id_item', 'reference item')
  , Field('quantity', 'decimal(16,6)')
  , auth.signature
)
# do not requires validators since theres is no public interface


supplier_format = '%(business_name)s %(tax_id)s'
db.define_table("supplier",
    Field("business_name", "string", default=None, label=T('Business Name')),
    Field("tax_id", "string", default="", label=T('Tax ID')),
    Field("id_address", "reference address", label=T('Address')),
    auth.signature, format=supplier_format)
db.supplier.business_name.requires = not_empty_requires
db.supplier.id_address.requires = IS_IN_DB(db(db.address.is_active == True), 'address.id', address_format)


db.define_table("purchase",
    Field("id_payment_opt", "reference payment_opt", label=T('Payment option')),
    Field("id_supplier", "reference supplier", label=T('Supplier')),
    Field("id_store", "reference store", label=T('Store')),
    Field("invoice_number", default=None, label=T('Invoice number')),
    Field("subtotal", "decimal(16,6)", default=0, label=T('Subtotal')),
    Field("total", "decimal(16,6)", default=0, label=T('Total')),
    Field("items_subtotal", "decimal(16,6)", default=0, label=T('Subotal'), readable=False, writable=False),
    Field("items_total", "decimal(16,6)", default=0, label=T('Total'), readable=False, writable=False),
    Field("shipping_cost", "decimal(16,6)", default=0, label=T('Shipping cost')),
    Field("tracking_number", "integer", default=None, label=T('Tracking number')),
    Field("is_done", "boolean", default=False, label=T('Done'), readable=False, writable=False),
    Field("purchase_xml", "upload", default=None, label=T('XML'), readable=False, writable=False),
    auth.signature)
db.purchase.id_supplier.requires = IS_IN_DB(db(db.supplier.is_active == True), 'supplier.id', supplier_format)
db.purchase.id_store.requires = IS_IN_DB(db(db.store.is_active == True), 'store.id', store_format)


db.define_table("bag",
    Field("id_store", "reference store", label=T('Store'))
    , Field("subtotal", "decimal(16,6)", default=0, label=T('Subtotal'))
    , Field("taxes", "decimal(16,6)", default=0, label=T('Taxes'))
    , Field("total", "decimal(16,6)", default=0, label=T('Total'))
    , Field("reward_points", "decimal(16,6)", default=0, label=T('Reward Point'))
    , Field("quantity", "decimal(16,6)", default=0, label=T('Quantity'))
    , Field("status", "integer", default=BAG_ACTIVE, label=T('Status'))
    , Field("is_sold", "boolean", default=False, label=T('Is sold'))
    , Field("is_paid", "boolean", default=False, label=T('Paid'))
    # this field is true when the items in the bag were removed from stock
    # this field is useful since there could be bags that are complete but not
    # delivered yet, like defered sales.
    , Field("is_delivered", "boolean", default=False, label=T('Delivered'))
    # used when the bag has been paid using stripe
    , Field("stripe_charge_id", default=None, label=T('Stripe charge id'))

    # deprecated soon
    , Field("completed", "boolean", default=False, label=T('Completed'))
    # this state is used to specify that the bag is being processed by the system
    , Field("is_on_hold", "boolean", default=False, label=T('On hold'))
    , auth.signature)


db.define_table("bag_item",
    Field("id_item", "reference item", label=T('Item')),
    Field("id_bag", "reference bag", label=T('Bag')),
    Field("quantity", "decimal(16,6)", default=1, label=T('Quantity')),
    # buy price + taxes and considering quantity
    Field("total_buy_price", "decimal(16,6)", default=None, label=T('Buy price')),
    Field("wavg_days_in_shelf", "integer", default=-1, label=T('Average shelf life')),
    # price minus discount
    Field("sale_price", "decimal(16,6)", default=None, label=T('Sale price')),
    Field("discount", "decimal(16,6)", default=0, label=T('Discount')),
    # list of item taxes at bag time, this string is something like
    # TAX:10,OTHER_TAX:20,  and it is created when the bag item is created
    Field("item_taxes", default=None, label=T('Item taxes'), readable=False, writable=False),
    # holds the actual taxes quantity based on the items taxes list
    Field("sale_taxes", "decimal(16,6)", default=None, label=T('Sale taxes')),
    Field("product_name", "string", default=None, label=T('Product name')),
    Field("reward_points", "decimal(16,6)", default=0),
    Field("sale_code", "string", default=None, label=T('Sale code')),
    Field("serial_number", "string", default=None, label=T('Serial number')),

    # used by bag items that are services (does not have inventory to specify who performed the service)
    Field("performed_by", "reference auth_user", default=None,
        label=T('Performed by')
    ),
    auth.signature
)


db.define_table(
  'product_loss_reason'
  , Field('name', label=T('name'))
  , auth.signature
)

db.define_table(
  'product_loss'
  , Field('id_store', 'reference store', label=T('Store'), readable=False, writable=False)
  , Field('id_bag', 'reference bag', label=T('Bag'), readable=False, writable=False)
  , Field('id_reason', "reference product_loss_reason", label=T('Reason'))
  , Field('notes', 'text', label=T('Notes'))
  , auth.signature
)
db.product_loss.id_reason.requires = IS_EMPTY_OR(IS_IN_DB(
    db, 'product_loss_reason.id', "%(name)s"
))


db.define_table(
    "cash_out"
    # -1 is used to calculate the sys_total for the first time
    , Field('sys_total', 'decimal(16,6)', default=-1, label=T('System total'))
    , Field('sys_cash', 'decimal(16,6)', default=0, label=T('System cash'))
    , Field('cash', 'decimal(16,6)', default=0, label=T('Physical cash'))
    , Field('id_seller', 'reference auth_user', label=T('Seller'))
    , Field('notes', 'text', label=T('Notes'))
    , Field('is_done', 'boolean', default=False, label=T('Is done'))
    , Field('start_date', 'datetime', label=T('Start date'))
    , Field('end_date', 'datetime', label=T('End date'))
    , auth.signature
)


db.define_table("sale",
    Field("id_bag", "reference bag", label=T('Bag'), readable=False, writable=False),
    Field("consecutive", "integer", default=0, label=T('Consecutive'), readable=False, writable=False),
    Field("subtotal", "decimal(16,6)", default=0, label=T('Subtotal'), readable=False, writable=False),
    Field("taxes", "decimal(16,6)", default=0, label=T('Taxes'), readable=False, writable=False),
    Field("total", "decimal(16,6)", default=0, label=T('Total'), readable=False, writable=False),

    Field("discount", "decimal(16,6)", default=0, label=T('Discount')),
    Field("discount_percentage", "decimal(16,6)", default=0, label=T('Discount percentage')),

    Field("quantity", "decimal(16,6)", default=0, label=T('Quantity'), readable=False, writable=False),
    Field("reward_points", "decimal(16,6)", default=0, label=T('Reward Points'), readable=False, writable=False),
    Field("id_client", "reference auth_user", default=None, label=T('Client')),
    Field("is_invoiced", "boolean", default=False, label=T('Is invoiced'), readable=False, writable=False),
    Field("id_store", "reference store", label=T('Store'), writable=False, readable=False),
    # true if the products in sale has been delivered and the sale has been paid
    Field("is_done", "boolean", default=False, writable=False, readable=False),
    # true if the sale has been defered for later payment
    Field("is_deferred", "boolean", default=False, writable=False, readable=False),
    Field("last_log_event", label=T('Last event')),
    Field("last_log_event_date", 'datetime', label=T('Last event date')),
    auth.signature
)
db.sale.id_client.requires = IS_EMPTY_OR(IS_IN_DB(db((db.auth_user.is_client == True) & (db.auth_user.registration_key == "")), 'auth_user.id', '%(email)s'))


db.define_table("sale_log",
    Field("id_sale", "reference sale", label=T('Sale')),
    Field("sale_event", "string", default=None, label=T('Event')),
    Field("event_date", "datetime", default=None, label=T('Date')),
    auth.signature)

db.define_table("credit_note",
    Field("id_sale", "reference sale", label=T('Sale')),
    Field("id_store", "reference store", label=T('Store')),
    Field("subtotal", "decimal(16,6)", default=None, label=T('Subtotal')),
    Field("total", "decimal(16,6)", default=None, label=T('Total')),
    Field("is_usable", "boolean", default=None, label=T('Is usable')),
    Field("code", "string", default=None, label=T('Code')),
    Field("id_wallet", "reference wallet", default=None, label=T('wallet')),
    auth.signature)

db.define_table("credit_note_item",
    Field("id_credit_note", "reference credit_note", label=T('Credit note')),
    Field("id_bag_item", "reference bag_item", label=T('Bag Item')),
    Field("quantity", "decimal(16,6)", default=None, label=T('Quantity')))


db.define_table(
  'sale_order'
  , Field('id_client', 'reference auth_user', default=None, label=T('Client'), readable=False, writable=False)
  , Field('id_bag', 'reference bag', label=T('Bag'), readable=False, writable=False)
  , Field('id_sale', 'reference sale', default=None, label=T('Sale'), readable=False, writable=False)
  , Field('id_store', 'reference store', label=T('Store'))
  # when the seller has sold out of stock items, the system creates a sale order for the defered sale
  , Field('is_for_defered_sale', 'boolean', default=False, label=T('Is for defered sale'), readable=False, writable=False)
  , Field('code', default=None, label=T('Code'), readable=False, writable=False)
  , Field('is_ready', 'boolean', default=False, label=T('Ready'), readable=False, writable=False)
  , auth.signature
)
db.sale_order.id_store.requires = IS_IN_DB(db, 'store.id')


db.define_table("inventory",
    Field("id_store", "reference store", label=T('Store')),
    Field("is_partial", "boolean", default=None, label=T('Is partial')),
    Field("is_done", "boolean", default=False, label=T('Is done')),
    Field("has_missing_items", "boolean", default=False, label=T('Has missing items')),
    auth.signature)

db.define_table("inventory_item",
    Field("id_inventory", "reference inventory", label=T('Inventory')),
    Field("id_item", "reference item", label=T('Item')),
    Field("system_qty", "integer", default=None, label=T('System quantity')),
    Field("physical_qty", "integer", default=None, label=T('Physical quantity')),
    Field("is_missing", "boolean", default=False, label=T('Is missing'))
)


db.define_table(
    'stock_transfer'
    , Field('id_store_from', 'reference store', label=T('From store'), writable=False, readable=False)
    , Field('id_store_to', 'reference store', label=T('To store'), writable=False, readable=False)
    , Field('id_bag', 'reference bag', label=T('bag'), writable=False, readable=False)
    , Field('is_done', 'boolean', default=False, label=T('Is done'), writable=False, readable=False)
    , auth.signature
)


db.define_table("stock_item",
    Field("id_purchase", "reference purchase", label=T('Purchase')),
    # When the item is returned we have to create a stock item with the
    # associated credit note
    Field("id_credit_note", "reference credit_note", label=T('Credit note')),
    # When there are more items than those registered by the system, we have to add stock related to that inventory
    Field("id_inventory", "reference inventory", label=T('Inventory')),
    Field("id_stock_transfer", "reference stock_transfer", label=T('Stock transfer')),
    # to simplify queries
    Field("id_store", "reference store", label=T('Store')),
    Field("id_item", "reference item", label=T('Item')),
    Field("purchase_qty", "decimal(16,6)", default=1, label=T('Purchase quantity')),
    Field("stock_qty", "decimal(16,6)", default=0, label=T('Stock quantity')),
    # the buy price
    Field("price", "decimal(16,6)", default=0, label=T('Price')),
    Field("taxes", "decimal(16,6)", default=0, label=T('Taxes')),
    Field("serial_numbers", "text", default=None, label=T('Serial numbers')),
    # base sale price, this will update the item base price when the purchase is applied
    Field("base_price", "decimal(16,6)", default=1, label=T('Base price')),
    Field("price2", "decimal(16,6)", default=0, label=T('Price') + '2'),
    Field("price3", "decimal(16,6)", default=0, label=T('Price') + '3'),
    auth.signature)


db.define_table(
    'stock_item_removal'
    , Field("id_store", "reference store", label=T('Store'))
    , Field('id_bag_item', 'reference bag_item', default=None)
    , Field('id_inventory_item', 'reference inventory_item', default=None)
    , Field('id_stock_item', 'reference stock_item', default=None)
    , Field('id_item', 'reference item', default=None)
    , Field('qty', 'decimal(16,6)', label=T('Quantity'))
    , auth.signature
)


db.define_table("payment",
    Field("id_payment_opt", "reference payment_opt", label=T('Payment option')),
    Field("id_sale", "reference sale", label=T('Sale')),
    # used to reference the payment before the sale creation
    Field("id_bag", "reference bag", label=T('bag')),
    Field("amount", "decimal(16,6)", default=0, label=T('Amount')),
    Field("account", "string", default=None, label=T('Account')),
    # reference to the wallet
    Field("wallet_code", default=None, label=T('Wallet code')),
    Field("change_amount", "decimal(16,6)", default=0, label=T('Change amount')),
    # only applicable if payment opt has credit days
    Field('is_settled', 'boolean', default=True, label=T('Is settled')),
    Field("epd", "date", label=T('Estimated payment date')),
    Field('settled_on', 'datetime', label=T('Settled on')),
    Field("stripe_charge_id", default=None, label=T('stripe_charge_id')),
    Field("is_updatable", 'boolean', default=True, label=T('Is updatable')),
    auth.signature)


db.define_table("item_image",
    Field("id_item", "reference item", label=T('Item'), readable=False, writable=False),
    Field("thumb", "upload", default=None, label=T('Thumbnail'), readable=False, writable=False, uploadfolder=os.path.join(request.folder, 'static/uploads'), autodelete=True),
    Field("sm", "upload", default=None, label=T('Small'), readable=False, writable=False, uploadfolder=os.path.join(request.folder, 'static/uploads'), autodelete=True),
    Field("md", "upload", default=None, label=T('Medium'), readable=False, writable=False, uploadfolder=os.path.join(request.folder, 'static/uploads'), autodelete=True),
    Field("lg", "upload", default=None, label=T('Image'), uploadfolder=os.path.join(request.folder, 'static/uploads'), autodelete=True),
)
db.item_image.lg.requires = IS_IMAGE(extensions=('jpg', 'jpeg', 'png'))


db.define_table(
    'offer_group'
    , Field('name', label=T('Name'))
    , Field('description', label=T('Description'))
    , Field("id_store", "reference store", label=T('Store'))
    , Field("starts_on", "datetime", default=None, label=T('Starts on'))
    , Field("ends_on", "datetime", default=None, label=T('Ends on'))
    , Field('bg_image', 'upload', label=T('Background image'), uploadfolder=os.path.join(request.folder, 'static/uploads'))
    # deprecated
    , Field("code", "string", default=None, label=T('Code'))
    , auth.signature
)
db.offer_group.name.requires = not_empty_requires
db.offer_group.id_store.requires = IS_EMPTY_OR(IS_IN_DB(db(db.store.is_active == True), 'store.id', '%(name)s'))
db.offer_group.bg_image.requires = highlight_image_validator


db.define_table(
    'discount'
    , Field('id_offer_group', 'reference offer_group')
    , Field('id_category', 'reference category')
    , Field('id_item', 'reference item')
    , Field('id_brand', 'reference brand')
    , Field("percentage", "integer", label=T('Percentage'))
    , Field("code", label=T('Code'))
    , Field("is_combinable", "boolean", default=False, label=T('Is combinable'))
    , Field("is_coupon", "boolean", default=False, label=T('Is coupon'))
    , auth.signature
)
db.discount.percentage.requires = IS_INT_IN_RANGE(1, 99)


db.define_table("account_receivable",
    Field("id_sale", "reference sale", label=T('Sale')),
    Field("is_settled", "boolean", default=False, label=T('Is settled')),
    auth.signature)


db.define_table("account_payable",
    Field("id_purchase", "reference purchase", label=T('Purchase')),
    Field("is_settled", "boolean", default=False, label=T('Is settled')),
    Field("epd", "date", label=T('Estimated payment date')),
    auth.signature)


db.define_table("tax_data",
    Field("tax_id", "integer", default=None, label=T('Tax ID')),
    Field("business_name", "string", default=None, label=T('Business Name')),
    Field("id_address", "reference address", label=T('Address')),
    auth.signature)


db.define_table("invoice",
    Field("id_sale", "reference sale", label=T('Sale')),
    Field("id_tax_data", "reference tax_data", label=T('Tax data')),
    Field("invoice_xml", "text", default=None, label=T('XML')),
    Field("uuid", "string", default=None, label=T('UUID')),
    Field("sat_seal", "string", default=None, label=T('SAT Seal')),
    Field("certification_date", "datetime", default=None, label=T('Certification date')),
    Field("folio", "integer", default=None, label=T('Folio')),
    Field("is_cancelled", "boolean", default=None, label=T('Is cancelled')),
    Field("cancel_date", "datetime", default=None, label=T('Cancel date')),
    Field("acknowledgement", "text", default=None, label=T('Acknowledgement')),
    auth.signature)

db.define_table("migration_table",
    Field("table_name",required=True,writable=False),
    Field("csv_file",type="upload",uploadfolder=request.folder+'/static/migrations/'),
    auth.signature
)

db.define_table("migration_dictionary",
    Field("id_migration_table"),
    Field("old_id",type="integer"),
    Field("new_id",type="integer")
)

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

from gluon.storage import Storage
from gluon import current

from common_utils import DQ
import os


FIELD_WRITE = 0
FIELD_APPEND = 1

class FieldParser:

    def _default_parse_function(data):
        return data


    def __init__(
        self,
        field, parse_function=_default_parse_function, field_type=FIELD_WRITE
    ):
        self.field = field
        self.parse_function = parse_function
        self.field_type = field_type


    def parse(self, data):
        return self.parse_function(data)





counter = 1300
items = []

brands = []
brands_map = {}

categories = []
categories_map = {}

used_bc = []


class LineParser:

    def __init__(self, spec):
        self.spec = spec

    def parse(self, line):
        d_item = Storage(is_active=True)

        values = map(
            lambda x : x.strip().lower().title(),
            line.decode('utf-8').split(',')
        )

        if len(values) != len(self.spec):
            raise ValueError('Invalid line or spec, sizes does not match')

        for index, value in enumerate(values):
            field_parser = self.spec[index]
            if not field_parser:
                continue
            parsed_value = field_parser.parse(value)
            if field_parser.field_type == FIELD_WRITE:
                d_item[field_parser.field] = parsed_value
            elif field_parser.field_type == FIELD_APPEND:
                if not d_item[field_parser.field]:
                    d_item[field_parser.field] = []
                d_item[field_parser.field].append(parsed_value)

        return d_item



def price_parser_function(data):
    return DQ(data)
    # item_params.base_price = item.base_price / DQ(1.16)


def name_parser_function(data):
    pass


BRANDS = {}
def brand_parser_function(data):
    db = current.db

    record = db( db.brand.name == data ).select().first()
    if record:
        return record.id
    new_id = db.brand.insert( name=data )
    return new_id



def categories_parser_function(data):
    pass




def trait_parser_function(container, trait_category_id, data):
    saved_id = container.get(data)
    if saved_id:
        return saved_id

    db = current.db
    record = db(
        (db.trait.id_trait_category == trait_category_id) &
        (db.trait.trait_option == data)
    ).select().first()
    if record:
        container[data] = record.id
        return record.id
    new_id = db.trait.insert(
        id_trait_category=trait_category_id, trait_option=data
    )
    container[data] = new_id
    return new_id


SIZES = {}
def size_parser_function(data):
    db = current.db
    size_trait_category = db(db.trait_category.name == 'talla').select().first()
    if not size_trait_category:
        size_trait_category = db.trait_category.insert(name='talla')
    return trait_parser_function(SIZES, size_trait_category, data)


COLORS = {}
def color_trait_parse_function(data):
    db = current.db
    color_trait_category = db(
        db.trait_category.name == 'color'
    ).select().first()
    if not color_trait_category:
        color_trait_category = db.trait_category.insert(name='talla')
    return trait_parser_function(COLORS, color_trait_category, data)



def file_parser_generator(file_path, line_parser):
    with open(file_path, 'r') as f:
        lines = f.readlines()
        for line in lines:
            if line == lines[0]:
                continue
            yield line_parser.parse(line)



def parse_file(filename, line_parser, item_format_function=None):
    """ Do not place data in the first row of the csv """

    db = current.db
    T = current.T
    request = current.request
    # return

    path = os.path.join(request.folder, 'private/data/%s' % filename)

    generator = file_parser_generator(path, line_parser)

    for item_data in generator:
        if item_format_function:
            item_format_function(item_data)
        print item_data
        db.item.insert(**item_data)



def parse():
    db = current.db

    def custom_category_parser_function(data):
        data = data[1:]

        record = db( db.category.name == data ).select().first()
        if record:
            return record.id
        new_id = db.category.insert( name=data )
        return new_id


    par_measure_unit = db.measure_unit.update_or_insert(
        name='par', symbol='par'
    )
    def item_custom_format(item_data):
        item_data.id_measure_unit = par_measure_unit
        item_data.allow_fractions = False
        item_data.taxes = []


    lparser = LineParser([
        FieldParser('categories',
            parse_function=custom_category_parser_function,
            field_type=FIELD_APPEND
        ),
        FieldParser('id_brand', parse_function=brand_parser_function),
        FieldParser('name'),
        FieldParser('traits', field_type=FIELD_APPEND,
            parse_function=color_trait_parse_function
        ),
        FieldParser('sku'),
        FieldParser('traits', field_type=FIELD_APPEND,
            parse_function=size_parser_function
        ),
        FieldParser('base_price', parse_function=price_parser_function),
        FieldParser('price2', parse_function=price_parser_function),
        FieldParser('price3', parse_function=price_parser_function)
    ])

    parse_file('precios_terra.csv', lparser, item_custom_format)



def parse_line(line, is_service=False):
    global counter

    item = Storage(is_active=True)
    values = map(lambda x : x.strip().lower().title(), line.decode('utf-8').split(','))
    item.name = values[0]
    item.description = values[1]


    item.brand = values[2]
    if item.brand and not item.brand in brands:
        brands.append(item.brand)

    item.categories = values[3].replace('Y', '')
    item_categories = []
    for cat in item.categories.split(':'):
        cat = cat.strip()
        for _cat in cat.split(' '):
            _cat = _cat.strip()
            _cat = 'Rostro' if _cat == 'Cara' else _cat
            if _cat:
                item_categories.append(_cat)
                if not _cat in categories:
                    if _cat:
                        categories.append(_cat)
    item.categories = item_categories

    m_unit = values[4].lower()
    is_piece = 'pz' in m_unit
    # dado que algunas unidades de medida estan especificadas como 500pz, removemos y almacenamos la cantidad en q_data y is_piece debe ser verdadero si el producto es pieza
    if is_piece:
        item.q_data = m_unit.replace('pz', '')
    item.is_piece = is_piece

    item.barcode = values[5].replace('#', '')
    if type(item.barcode) == unicode:
        # print item.barcode
        item.barcode = item.barcode.replace(unichr(241), 'n')
    if not item.barcode or item.barcode in used_bc:
        # barcode generator
        bc = ''
        for i in xrange(4): bc += str(randint(0, 9));
        bc = u"{0}{1}".format(bc, counter)
        item.barcode = bc
        if item.barcode in used_bc:
            bc = ''
            while item.barcode in used_bc:
                for i in xrange(4): bc += str(randint(0, 9));
                bc = u"{0}{1}".format(bc, counter)
                item.barcode = bc
    counter += 1
    item.barcode = item.barcode.encode('ascii')
    used_bc.append(item.barcode)

    try:
        item.base_price = DQ(values[6])
        if not item.base_price:
            raise Exception
    except:
        item.base_price = DQ(1)
        item.is_active = False
    try:
        item.buy_price = DQ(values[7])
    except:
        item.buy_price = DQ(1)

    try:
        item.stock = DQ(values[8])
    except:
        item.stock = DQ(0)

    item.has_inventory = not is_service

    return item



def config(filename, insert=False, validate=False):
    """ Do not place data in the first row of the csv """

    db = current.db
    T = current.T
    request = current.request
    # return

    path = os.path.join(request.folder, 'private/data/%s' % filename)
    with open(path, 'r') as f:
        lines = f.readlines()
        for line in lines:
            if line == lines[0]:
                continue
            item = parse_line(line, True)
            items.append(item)

    # add brands to db
    for brand in brands:
        brand_id = db(db.brand.name == brand).select(db.brand.id).first()
        if not brand_id:
            brand_id = db.brand(db.brand.insert(name=brand))
        brands_map[brand] = brand_id.id

    for category in categories:
        cat_id = db(db.category.name == category).select(db.category.id).first()
        if not cat_id:
            cat_id = db.category(db.category.insert(name=category))
        categories_map[category] = cat_id.id

    # measure_units
    pieza_mu_id = db(db.measure_unit.name == 'Pieza').select().first()
    if not pieza_mu_id:
        pieza_mu_id = db.measure_unit(db.measure_unit.insert(name='Pieza', symbol='pz'))


    iva_id = db(db.tax.name == 'I.V.A.').select().first()
    if not iva_id:
        iva_id = db.tax(db.tax.insert(name='I.V.A.', symbol='%', percentage=16))
    iva_id = iva_id.id

    # add items
    no_brand = db(db.brand.name == T('no brand')).select(db.brand.id).first()
    for item in items:
        item_params = Storage()
        item_params.name = item.name
        if item.brand:
            item_params.id_brand = brands_map[item.brand]
        else:
            item_params.id_brand = no_brand.id
        item_params.categories = []
        for cat in item.categories:
            item_params.categories.append(categories_map[cat])
        item_params.description = item.description
        item_params.sku = str(item.barcode)
        item_params.is_bundle = False
        item_params.has_inventory = item.has_inventory
        item_params.base_price = item.base_price / DQ(1.16)
        if item.is_piece:
            item_params.id_measure_unit = pieza_mu_id.id
        else:
            item_params.id_measure_unit = pieza_mu_id.id
        if item.q_data:
            # item_params.extra_data1 = " Contiene %s piezas" % item.q_data
            item_params.description += "\n - Contiene %s piezas" % item.q_data
        item_params.taxes = [iva_id]
        item_params.allow_fractions = False
        item_params.is_returnable = False
        item_params.is_active = item.is_active

        # print dict(item_params)
        if insert and not validate:
            r = db.item.insert(**item_params)
            if r.errors:
                print r.errors
                continue
            # create purchase item
            # if item_params.is_active and item_params.has_inventory:
            #     db.stock_item.insert(id_purchase=first_purchase_id, id_item=r, id_store=matrix_store.id, price=item.buy_price)
            #     print item_params
            #     db.commit()

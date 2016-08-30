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
FIELD_CONCAT = 2

FIELD_MODE_APPEND = 0
FIELD_MODE_PREPEND = 1

class FieldParser:

    def _default_parse_function(data):
        return data


    def __init__(
        self,
        field, parse_function=_default_parse_function, field_type=FIELD_WRITE,
        mode=None
    ):
        self.field = field
        self.parse_function = parse_function
        self.field_type = field_type
        self.mode = mode


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

        values = map( lambda x : x.strip(), line.decode('utf-8').split(',') )

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

            elif field_parser.field_type == FIELD_CONCAT:
                if not d_item[field_parser.field]:
                    d_item[field_parser.field] = parsed_value
                else:
                    if field_parser.mode == FIELD_MODE_APPEND:
                        d_item[field_parser.field] += ' ' + parsed_value
                    elif field_parser.mode == FIELD_MODE_PREPEND:
                        d_item[field_parser.field] = parsed_value + ' ' + d_item[field_parser.field]


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



def category_parser_function(data):
    db = current.db

    record = db( db.category.name == data ).select().first()
    if record:
        return record.id
    new_id = db.category.insert( name=data )
    return new_id


def parse():
    db = current.db

    def custom_catalog_parser_function(data):
        data = data[1:]
        return data

    par_measure_unit = db(db.measure_unit.name == 'par').select().first()
    if not par_measure_unit:
        par_measure_unit = db.measure_unit.insert(
            name='par', symbol='par'
        )
    piece_measure_unit = db(db.measure_unit.name == 'par').select().first()
    if not piece_measure_unit:
        piece_measure_unit = db.measure_unit.insert(
            name='pieza', symbol='pieza'
        )
    def item_custom_format(item_data):
        item_data.id_measure_unit = par_measure_unit
        item_data.allow_fractions = False
        item_data.taxes = []


    lparser = LineParser([
        FieldParser('name',
            parse_function=custom_catalog_parser_function,
            field_type=FIELD_CONCAT, mode=FIELD_MODE_PREPEND
        ),
        FieldParser('id_brand', parse_function=brand_parser_function),
        FieldParser('name', field_type=FIELD_CONCAT, mode=FIELD_MODE_APPEND ),
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


    cklass_brand = db(db.brand.name == 'Cklass').select().first()
    if not cklass_brand:
        cklass_brand = db.brand.insert(name='Cklass')

    def cklass_item_custom_format(item_data):
        item_custom_format(item_data)
        item_data.id_brand = cklass_brand


    lparser_cklass = LineParser([
        FieldParser('name', field_type=FIELD_CONCAT, mode=FIELD_MODE_APPEND ),
        FieldParser('traits', field_type=FIELD_APPEND,
            parse_function=color_trait_parse_function
        ),
        FieldParser('traits', field_type=FIELD_APPEND,
            parse_function=size_parser_function
        ),
        FieldParser('base_price', parse_function=price_parser_function),
        None,
        FieldParser('sku'),
        FieldParser('name', field_type=FIELD_CONCAT, mode=FIELD_MODE_PREPEND ),
        None,
        None
    ])

    parse_file('precios_terra.csv', lparser, item_custom_format)
    parse_file('cklass.csv', lparser_cklass, cklass_item_custom_format)

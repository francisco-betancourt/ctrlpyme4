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


class LineParser:

    def __init__(self, spec):
        self.spec = spec


    def _apply_parser(self, f_parser, value, d_item):
        parsed_value = f_parser.parse(value)

        if f_parser.field_type == FIELD_WRITE:
            d_item[f_parser.field] = parsed_value

        elif f_parser.field_type == FIELD_APPEND:
            if not d_item[f_parser.field]:
                d_item[f_parser.field] = []
            d_item[f_parser.field].append(parsed_value)

        elif f_parser.field_type == FIELD_CONCAT:
            if not d_item[f_parser.field]:
                d_item[f_parser.field] = parsed_value
            else:
                if f_parser.mode == FIELD_MODE_APPEND:
                    d_item[f_parser.field] += ' ' + parsed_value
                elif f_parser.mode == FIELD_MODE_PREPEND:
                    d_item[f_parser.field] = parsed_value + ' ' + d_item[f_parser.field]


    def parse(self, line):
        d_item = Storage(is_active=True)

        values = map( lambda x : x.strip(), line.decode('utf-8').split(',') )

        if len(values) != len(self.spec):
            raise ValueError('Invalid line or spec, sizes does not match')

        for index, value in enumerate(values):
            field_parser = self.spec[index]

            parsers = []
            if type(field_parser) is list:
                parsers = field_parser
            else:
                parsers.append(field_parser)

            for parser in parsers:
                if not parser:
                    continue
                self._apply_parser(parser, value, d_item)

        return d_item



def price_parser_function(data):
    return DQ(data)


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
SIZE_TRAIT_CATEGORY = None
def size_parser_function(data):
    db = current.db
    if not SIZE_TRAIT_CATEGORY:
        SIZE_TRAIT_CATEGORY = db(
            db.trait_category.name == 'talla'
        ).select().first()
    if not SIZE_TRAIT_CATEGORY:
        SIZE_TRAIT_CATEGORY = db.trait_category.insert(name='talla')
    return trait_parser_function(SIZES, SIZE_TRAIT_CATEGORY, data)


class SizeFieldParser(FieldParser):
    SIZES = {}
    SIZE_TRAIT_CATEGORY = None

    def __init__( self ):
        self.field = "traits"
        self.field_type = FIELD_APPEND


    def parse(self, data):
        db = current.db
        if not self.SIZE_TRAIT_CATEGORY:
            self.SIZE_TRAIT_CATEGORY = db(
                db.trait_category.name == 'talla'
            ).select().first()
        if not self.SIZE_TRAIT_CATEGORY:
            self.SIZE_TRAIT_CATEGORY = db.trait_category.insert(name='talla')
        return trait_parser_function(
            self.SIZES, self.SIZE_TRAIT_CATEGORY, data
        )



class ColorFieldParser(FieldParser):
    COLORS = {}
    COLOR_TRAIT_CATEGORY = None

    def __init__( self ):
        self.field = "traits"
        self.field_type = FIELD_APPEND


    def parse(self, data):
        db = current.db
        if not self.COLOR_TRAIT_CATEGORY:
            self.COLOR_TRAIT_CATEGORY = db(
                db.trait_category.name == 'color'
            ).select().first()
        if not self.COLOR_TRAIT_CATEGORY:
            self.COLOR_TRAIT_CATEGORY = db.trait_category.insert(name='color')
        return trait_parser_function(
            self.COLORS, self.COLOR_TRAIT_CATEGORY, data
        )



def file_parser_generator(file_path, line_parser):
    with open(file_path, 'r') as f:
        lines = f.readlines()
        for line in lines:
            if line == lines[0]:
                continue
            yield line_parser.parse(line)



def parse_file(filename, line_parser, item_format_function=None):
    """ DO NOT place data in the first row of the csv """

    db = current.db
    T = current.T
    request = current.request
    # return

    path = os.path.join(request.folder, 'private/data/%s' % filename)

    generator = file_parser_generator(path, line_parser)

    commit_max = 100
    counter = 0

    for item_data in generator:
        if item_format_function:
            item_format_function(item_data)
        print item_data
        db.item.insert(**item_data)
        if counter % commit_max == 0:
            db.commit()
        counter += 1
    db.commit()



def category_parser_function(data):
    db = current.db

    record = db( db.category.name == data ).select().first()
    if record:
        return record.id
    new_id = db.category.insert( name=data )
    return new_id

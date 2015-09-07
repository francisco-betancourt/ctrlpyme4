#! /usr/bin/env python
# -*- coding: utf8 -*-

def index():
    grid=SQLFORM.grid(db.brand)
    return dict(grid=grid)
    

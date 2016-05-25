# style related settup
from gluon import current
from gluon.html import XML
from common_utils import css_path, js_path


def PRELOAD(enable_bootstrap=True,
            enable_treeview=True,
            enable_css_item_card=True,
            enable_navbar=True,
            enable_supert=True,
            enable_calendar=True,
            enable_css_ticket=True):

    auth = current.auth

    PAGE_STYLE_STRING = ''
    if enable_bootstrap:
        with open(css_path('bootstrap.min.css'), 'r') as f:
            PAGE_STYLE_STRING += f.read()
        if enable_treeview:
            with open(css_path('bootstrap-treeview.min.css'), 'r') as f:
                PAGE_STYLE_STRING += f.read()
    with open(css_path('ctrlpyme.css'), 'r') as f:
        PAGE_STYLE_STRING += f.read()
    if enable_css_item_card:
        with open(css_path('item_card.css'), 'r') as f:
            PAGE_STYLE_STRING += f.read()
    if enable_navbar:
        with open(css_path('navbar.css'), 'r') as f:
            PAGE_STYLE_STRING += f.read()
    if enable_supert:
        with open(css_path('supert.css'), 'r') as f:
            PAGE_STYLE_STRING += f.read()
    if enable_calendar:
        with open(css_path('calendar.css'), 'r') as f:
            PAGE_STYLE_STRING += f.read()
    if enable_css_ticket:
        with open(css_path('ticket.css'), 'r') as f:
            PAGE_STYLE_STRING += f.read()

    current.css_style = XML(PAGE_STYLE_STRING)


    PAGE_HEAD_SCRIPT_STRING = ''
    with open(js_path('modernizr-2.8.3.min.js'), 'r') as f:
        PAGE_HEAD_SCRIPT_STRING += f.read()
    with open(js_path('jquery.js'), 'r') as f:
        PAGE_HEAD_SCRIPT_STRING += f.read()
    if enable_calendar:
        with open(js_path('calendar.js'), 'r') as f:
            PAGE_HEAD_SCRIPT_STRING += f.read()
    with open(js_path('web2py.js'), 'r') as f:
        PAGE_HEAD_SCRIPT_STRING += f.read()
    current.head_js = XML(PAGE_HEAD_SCRIPT_STRING)


    # optional scripts
    PAGE_SCRIPT_STRING = ''
    if enable_supert:
        with open(js_path('supert.js'), 'r') as f:
            PAGE_SCRIPT_STRING += f.read()
    if enable_bootstrap:
        with open(js_path('bootstrap.min.js'), 'r') as f:
            PAGE_SCRIPT_STRING += f.read()
        with open(js_path('web2py-bootstrap3.js'), 'r') as f:
            PAGE_SCRIPT_STRING += f.read()
        if enable_treeview:
            with open(js_path('bootstrap-treeview.min.js'), 'r') as f:
                PAGE_SCRIPT_STRING += f.read()
    if enable_navbar:
        with open(js_path('navbar.js'), 'r') as f:
            PAGE_SCRIPT_STRING += f.read()
    current.js = XML(PAGE_SCRIPT_STRING)

    return PAGE_STYLE_STRING, PAGE_HEAD_SCRIPT_STRING, PAGE_SCRIPT_STRING

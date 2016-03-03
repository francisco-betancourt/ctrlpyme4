# settings list

from datetime import timedelta

COMPANY_NAME = 'CtrlPyME'
COMPANY_SLOGAN = 'Press Ctrl + PyME to begin.'
COMPANY_LOGO_URL = ''

# the workflow determines how the employees will interact with the application
COMPANY_WORKFLOW = FLOW_BASIC

CASH_OUT_INTERVAL = timedelta(days=1)

EXTRA_FIELD_1_NAME = None
EXTRA_FIELD_2_NAME = None
EXTRA_FIELD_3_NAME = None

# if set true, only those users who have been created by the admin will have access to the online store.
USE_CLIENTS_WHITELIST = True

TICKET_FOOTER = T('This will be a ticket footer... soon')

# PAPER metrics in centimeters
PAPER_WIDTH = 21.59
PAPER_HEIGHT = 27.94
PAPER_MARGIN_TOP = 1
PAPER_MARGIN_RIGHT = 1
PAPER_MARGIN_BOTTOM = 1
PAPER_MARGIN_LEFT = 1

# labels, metrics in centimeters
LABEL_SPACE_X = .5
LABEL_SPACE_Y = .5
LABEL_COLS = 3
LABEL_ROWS = 8
LABEL_SHOW_ITEM_NAME = True
LABEL_SHOW_PRICE = True

PRIMARY_COLOR = '#505050'
PRIMARY_COLOR_TEXT = '#FFFFFF'

ACCENT_COLOR = '#2375CA'
ACCENT_COLOR_TEXT = '#FFFFFF'

BASE_COLOR = '#F3F3F3'
BASE_COLOR_TEXT = '#444'


main_settings = db(db.settings.id_store == None).select().first()
if main_settings:
    if main_settings.company_name:
        COMPANY_NAME = main_settings.company_name
    if main_settings.company_slogan:
        COMPANY_SLOGAN = main_settings.company_slogan
    if main_settings.company_logo:
        COMPANY_LOGO_URL = main_settings.company_logo
    # if main_settings.workflow:
    #     COMPANY_WORKFLOW = main_settings.workflow
    if main_settings.extra_field_1:
        EXTRA_FIELD_1_NAME = main_settings.extra_field_1
    if main_settings.extra_field_2:
        EXTRA_FIELD_2_NAME = main_settings.extra_field_2
    if main_settings.extra_field_3:
        EXTRA_FIELD_3_NAME = main_settings.extra_field_3

    if main_settings.clients_whitelist:
        USE_CLIENTS_WHITELIST = main_settings.clients_whitelist

    if main_settings.ticket_footer:
        TICKET_FOOTER = main_settings.ticket_footer

    if main_settings.primary_color:
        PRIMARY_COLOR = main_settings.primary_color
    if main_settings.primary_color_text:
        PRIMARY_COLOR_TEXT = main_settings.primary_color_text
    if main_settings.accent_color:
        ACCENT_COLOR = main_settings.accent_color
    if main_settings.accent_color_text:
        ACCENT_COLOR_TEXT = main_settings.accent_color_text
    if main_settings.base_color:
        BASE_COLOR = main_settings.base_color
    if main_settings.base_color_text:
        BASE_COLOR_TEXT = main_settings.base_color_text


LABEL_WIDTH = (PAPER_WIDTH - (PAPER_MARGIN_LEFT + PAPER_MARGIN_RIGHT + LABEL_SPACE_X * (LABEL_COLS - 1))) / LABEL_COLS
LABEL_HEIGHT = (PAPER_HEIGHT - (PAPER_MARGIN_TOP + PAPER_MARGIN_BOTTOM + LABEL_SPACE_Y * (LABEL_ROWS - 1))) / LABEL_ROWS

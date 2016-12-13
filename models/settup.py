from common_utils import *
from html_utils import *
from item_utils import item_barcode
from constants import *

from analysis_utils import TIME_MODES

enable_bootstrap = True
enable_treeview = True
enable_css_item_card = True
enable_navbar = True
enable_supert = True
enable_calendar = True
enable_css_ticket = True
enable_item_cards = True

MEMBERSHIPS = dict([(v, True) for v in auth.user_groups.values()])

item_options = []
if MEMBERSHIPS.get('Employee'):
    if (MEMBERSHIPS.get('Items info') or
        MEMBERSHIPS.get('Items management') or
        MEMBERSHIPS.get('Items prices')
    ):
        item_options.append(( T('Update'), URL('item', 'update') ))
        item_options.append(( T('Print labels'), URL('item', 'labels') ))
        item_options.append(( T('Add images'), URL('item_image', 'create') ))

    if MEMBERSHIPS.get('Analytics'):
        item_options.append((T('Analysis'), URL('analytics', 'item_analysis')))



EXPIRATION_DAYS = 0
EXPIRED = True
file_path = os.path.join(request.folder, 'private/', 'expiration_date')
with open(file_path, 'r') as f:
    from datetime import datetime, timedelta
    year, month, day = map(int, f.read().replace('\n', '').split('-'))
    expiration_date = datetime(year, month, day)

    EXPIRATION_DAYS = (expiration_date - request.now).days
    if EXPIRATION_DAYS > 0:
        EXPIRED = False

current.EXPIRATION_DAYS = EXPIRATION_DAYS

from common_utils import *
from html_utils import *
from bag_utils import auto_bag_selection
from item_utils import item_barcode
from constants import *

# avoid excesive memory usage, this is a workaround since web2py or the application seems to be consuming a lot of memory, TODO: further investigation of the problem.
import gc
gc.collect()

enable_bootstrap = True
enable_treeview = True
enable_css_item_card = True
enable_navbar = True
enable_supert = True
enable_calendar = True
enable_css_ticket = True
enable_item_cards = True

item_options = []
if auth.has_membership('Employee'):
    if (auth.has_membership('Items info') or
        auth.has_membership('Items management') or
        auth.has_membership('Items prices')
    ):
        item_options.append(( T('Update'), URL('item', 'update') ))
        item_options.append(( T('Print labels'), URL('item', 'labels') ))
        item_options.append(( T('Add images'), URL('item_image', 'create') ))

    if auth.has_membership('Analytics'):
        item_options.append((T('Analysis'), URL('analytics', 'item_analysis')))

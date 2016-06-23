from common_utils import *
from html_utils import *
from bag_utils import auto_bag_selection
from item_utils import item_barcode
from constants import *

# avoid excesive memory usage, this is a workaround since web2py or the application seems to be consuming a lot of memory, TODO: further investigation of the problem.
import gc
gc.collect()

enable_bootstrap=True
enable_treeview=True
enable_css_item_card=True
enable_navbar=True
enable_supert=True
enable_calendar=True
enable_css_ticket=True

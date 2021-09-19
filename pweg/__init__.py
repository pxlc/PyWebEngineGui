
from .WebEngineDialogBase import WebEngineDialogBase
from .PluginBase import PluginBase

from .util import launch_main_app, launch_as_dialog, register_op, register_plugin_op

from .util import inside_maya_dcc, get_maya_main_window
from .util import inside_houdini_dcc, get_houdini_main_window
from .util import inside_nuke_dcc, get_nuke_main_window
from .util import inside_katana_dcc, get_katana_main_window

import os
PWEG_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))).replace('\\', '/')

def get_qtpy_package():
    # import qtpy package (abstaction for PySide2, PyQt5) and return
    import sys
    sys.path.insert(0, '%s/thirdparty_packages' % PWEG_ROOT)  # to include QtPy package
    import qtpy
    return qtpy



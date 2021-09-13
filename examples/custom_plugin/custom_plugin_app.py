# -------------------------------------------------------------------------------
# MIT License
#
# Copyright (c) 2021 pxlc@github
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
# -------------------------------------------------------------------------------

import os
import sys
import json
import logging

APP_ROOT = os.path.dirname(os.path.abspath(__file__)).replace('\\', '/')
APP_PLUGINS_PATH = '%s/plugins' % APP_ROOT

# Set things up to be able to point to plugins inside of this app folder
os.environ['PWEG_PLUGINS_PATH'] = os.pathsep.join([APP_PLUGINS_PATH, os.getenv('PWEG_PLUGINS_PATH')]) \
                                    if os.getenv('PWEG_PLUGINS_PATH') else APP_PLUGINS_PATH

from PyWebEngineGui.pweg import WebEngineDialogBase, register_op, launch_main_app


class CustomPluginApp(WebEngineDialogBase):

    def __init__(self, parent=None, html_filepath='', app_title='', width=500, height=200,
                 log_level_str='INFO', log_to_shell=True):

        # Plugin requests MUST be specified BEFORE calling the super __init__() method
        NEEDED_PLUGINS = ['MyFirstPlugin']

        super(CustomPluginApp, self).__init__(parent=parent, app_module_path=os.path.abspath(__file__),
                                              html_filepath='', app_title=app_title,
                                              width=width, height=height,

                                              requested_plugins_list=NEEDED_PLUGINS,

                                              override_session_log_filepath='',
                                              log_level_str=log_level_str,
                                              log_to_shell=log_to_shell)

        # Do any required data set-up for your app here
        pass

    # --------------------------------------------------------------------------------------------------------
    # "setup_extra_template_vars()" is a REQUIRED override method
    #
    #  Establish any values for template vars in this method that you need to use in your HTML template file.
    # --------------------------------------------------------------------------------------------------------
    def setup_extra_template_vars(self):

        return {}

    # --------------------------------------------------------------------------------------------------------
    #  Register any callback op handler methods in this way ...
    #
    #      @register_op
    #      def my_op_handler(self, op_data):
    #          # op_data is data dict received from JavaScript side
    #          for op_data_key in sorted(op_data.keys()):
    #              self.info('    %s = %s' % (op_data_key, op_data[op_data_key]))
    #
    #    NOTE: DO NOT register an op handler method named "print_message" (that is a default one
    #          provided by the base class)
    # --------------------------------------------------------------------------------------------------------

    @register_op
    def test_one_js_click(self, op_data):

        self.info('')
        self.info(':: got op "test_one_js_click" with data "{0}"'.format(op_data))
        self.info('')

        self.call_js_op('test_one', {'x': 999, 'y': 808, 'z': 345})


if __name__ == '__main__':

    sys.exit(launch_main_app(CustomPluginApp, app_title='Custom Plugin App Example', width=600, height=400))



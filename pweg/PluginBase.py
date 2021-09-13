
from PySide2.QtWidgets import QApplication


class PluginBase(object):

    def __init__(self):

        pass

    def _connect_to_app(self, plugin_name, app_call_js_op, debug, info, warning, error, is_modal_dialog):

        self.plugin_name = plugin_name

        self.app_functions = {
           'debug': debug,
           'info': info,
           'warning': warning,
           'error': error,
           'call_js_op': app_call_js_op,
        }

        self.is_modal_dialog = is_modal_dialog

    def debug(self, msg):
        self.app_functions['debug'](msg)

    def info(self, msg):
        self.app_functions['info'](msg)

    def warning(self, msg):
        self.app_functions['warning'](msg)

    def error(self, msg):
        self.app_functions['error'](msg)

    def critical(self, msg):
        self.app_functions['critical'](msg)

    def call_plugin_js_op(self, plugin_js_function_name, op_data):

        plugin_op = 'Plugin|%s|%s' % (self.plugin_name, plugin_js_function_name)
        self.app_functions['call_js_op'](plugin_op, op_data)

    def process_events(self):
        if self.is_modal_dialog:
            QApplication.instance().processEvents()

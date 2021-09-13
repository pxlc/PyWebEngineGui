
import os
import sys
import json
import base64
import jinja2
import getpass
import logging
import datetime

from PySide2.QtWidgets import QApplication, QWidget, QDialog, QVBoxLayout
from PySide2.QtWebEngineWidgets import QWebEngineView, QWebEnginePage
from PySide2.QtWebChannel import QWebChannel
from PySide2.QtCore import QUrl, Slot, QObject, QUrl, Qt, QMargins

from .util import register_op
from .PluginManager import PluginManager

PWEG_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))).replace('\\', '/')


class JSPythonCallHandler(QObject):

    def __init__(self, *args, **kwargs):
        super(JSPythonCallHandler, self).__init__(*args, **kwargs)
        self.op_registry_d = None

    def set_op_registry(self, op_registry_d):
        self.op_registry_d = op_registry_d

    @Slot(str, result=str)
    def to_python(self, data_d_str):
        if not self.op_registry_d:
            return json.dumps({
                        'ret_status': 'ERROR', 'message': 'Command Registry has not been set'
                   })

        data_d = json.loads(data_d_str)
        op = data_d.get('op')
        op_data = data_d.get('op_data')

        if op is None:
            return json.dumps({
                        'ret_status': 'ERROR', 'message': 'No "op" key specified or "op" value is null/None'
                   })
        if op not in self.op_registry_d:
            return json.dumps({
                        'ret_status': 'ERROR', 'message': '"op" name "%s" is not registered' % op
                   })
        op_fn = self.op_registry_d[op]
        result_data = op_fn(op_data)
        return json.dumps(result_data)


class WebEnginePage(QWebEnginePage):

    def __init__(self, *args, **kwargs):
        super(WebEnginePage, self).__init__(*args, **kwargs)

    def javaScriptConsoleMessage(self, level, message, lineNumber, sourceId):
        print("WebEnginePage Console: ", level, message, lineNumber, sourceId)


class WebEngineDialogBase(QDialog):

    def __init__(self, parent=None, app_module_path='', html_filepath='', app_title='', width=500, height=200,
                 requested_plugins_list=None, override_session_log_filepath='',
                 log_level_str='INFO', log_to_shell=True, is_modal_dialog=False):

        super(WebEngineDialogBase, self).__init__(parent)

        self.resize(width, height)

        self.pweg_root = PWEG_ROOT
        self.app_title = app_title or self.__class__.__name__

        self.app_module_path = app_module_path.replace('\\', '/')
        self.app_root = os.path.dirname(app_module_path)

        self.html_filepath = html_filepath.replace('\\', '/').replace('<APP_ROOT>', self.app_root) \
                                if html_filepath \
                                else '%s_TEMPLATE.html' % os.path.splitext(self.app_module_path)[0]

        self.is_modal_dialog = is_modal_dialog

        self.setWindowTitle(self.app_title)
        self.setModal(self.is_modal_dialog)

        self.requested_plugins_list = requested_plugins_list or []

        # Use a webengine view
        self.web_engine_view = QWebEngineView(parent=self)

        # Now get rid of question mark icon to the left of the window close icon (this is just a Windows thing)
        if sys.platform == 'win32':
            self.setWindowFlags(self.windowFlags() ^ Qt.WindowContextHelpButtonHint)

        # Set up JS-to-Python communication bridge via web channel
        self.js_python_call_handler = JSPythonCallHandler()
        self.channel = QWebChannel()

        # Make the handler object available, naming it "python_bridge"
        self.channel.registerObject("python_bridge", self.js_python_call_handler)

        # Use a custom page that prints console messages to make debugging easier
        self.web_engine_page = WebEnginePage()
        self.web_engine_page.setWebChannel(self.channel)
        self.web_engine_view.setPage(self.web_engine_page)

        # Create layout and add widgets
        layout = QVBoxLayout()
        layout.setContentsMargins(QMargins(0, 0, 0, 0))
        layout.addWidget(self.web_engine_view)

        # Set dialog layout
        self.setLayout(layout)

        # Set up other things
        self.session_start_dt_str = datetime.datetime.now().strftime('%Y%m%d-%H%M%S-%f')[:-3]

        bits = self.get_app_title().split()
        self.app_code = ''.join([b.lower().capitalize() for b in bits])

        self.session_id = 'pxlc_PWEG_%s_%s_%s' % (self.app_code, getpass.getuser(), self.session_start_dt_str)

        _temp_root = os.path.expandvars('${HOME}/.pxlc_temp')
        if sys.platform == 'win32':
            _temp_root = '%s/_pxlc_temp' % os.path.expandvars(
                                                '${USERPROFILE}/AppData/Local/Temp').replace('\\', '/')
        self.session_temp_root = '%s/%s' % (_temp_root, self.session_id)
        os.makedirs(self.session_temp_root)

        # Set up log file for the session
        self.log_filepath = '%s/session_logging.log' % self.session_temp_root
        if override_session_log_filepath:
            self.log_filepath = override_session_log_filepath
        _log_dirpath = os.path.dirname(self.log_filepath)

        if not os.path.exists(_log_dirpath):
            os.makedirs(_log_dirpath)

        # Set up logging
        log_level_map = {
            'DEBUG': logging.DEBUG, 'INFO': logging.INFO, 'WARNING': logging.WARNING, 'ERROR': logging.ERROR,
            'CRITICAL': logging.CRITICAL
        }
        log_level = logging.ERROR
        if log_level_str in log_level_map:
            log_level = log_level_map.get(log_level_str)

        self.logger = logging.getLogger('{a}{dt}'.format(a=self.app_code,
                                                         dt=self.session_start_dt_str.replace('_','')))
        self.logger.setLevel( log_level )
        self._setup_logger(self.logger, self.log_filepath, log_level, log_to_shell=log_to_shell)

        # Set up Plugin Manager
        all_plugins_html_str = ''
        self.plugin_manager = None

        if requested_plugins_list:
            self.plugin_manager = PluginManager(self, requested_plugins_list)
            all_plugins_html_str = self.plugin_manager.get_all_plugins_html_str()

        # Set up HTML template vars before loading html file
        self.html_template_vars = {
            'APP_ROOT': self.app_root,
            'APP_TITLE': self.app_title,
            'PWEG_ROOT': PWEG_ROOT,
        }
        self.html_template_vars.update(self.setup_extra_template_vars())

        self.load_html_template_file(self.html_filepath, all_plugins_html=all_plugins_html_str)

        # Set up op regsitry of method calls to be called from JavaScript
        self.op_registry = {}
        self._register_ops()

        if self.plugin_manager:
            self.plugin_manager.register_all_plugin_ops(self.op_registry)

        self.js_python_call_handler.set_op_registry(self.op_registry)

    def _setup_logger(self, logger, log_filepath, logging_level, log_to_shell=False):

        log_formatter = logging.Formatter("%(asctime)s [%(levelname)-5.5s]:  %(message)s")

        file_handler = logging.FileHandler(log_filepath)
        file_handler.setLevel(logging_level)
        file_handler.setFormatter(log_formatter)

        logger.addHandler(file_handler)

        if log_to_shell:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(logging_level)
            console_handler.setFormatter(log_formatter)

            logger.addHandler(console_handler)

    def _register_ops(self):

        # set up op registry here
        for attr_name in dir(self):
            attr = getattr(self, attr_name)
            if 'bound method' in str(attr) and hasattr(attr, '_op_name'):
                op_name = attr._op_name.split('.')[1] if '.' in attr._op_name else attr._op_name
                op_method = attr
                print('    adding op: %s' % op_name)
                self.op_registry[op_name] = op_method

    def get_plugin_instance(self, plugin_name):

        if not self.plugin_manager:
            return None
        return self.plugin_manager.get_plugin_instance(plugin_name)

    def debug(self, msg):
        self.logger.debug(msg)

    def info(self, msg):
        self.logger.info(msg)

    def warning(self, msg):
        self.logger.warning(msg)

    def error(self, msg):
        self.logger.error(msg)

    def get_pweg_root(self):

        return self.pweg_root

    def get_app_root(self):

        return self.app_root

    def get_app_title(self):

        return self.app_title

    def get_app_code(self):

        return self.app_code

    def get_session_temp_root(self):

        return self.session_temp_root

    def get_session_log_filepath(self):

        return self.log_filepath

    def _load_html_file_url(self, filepath):

        url = QUrl.fromLocalFile(filepath)
        self.web_engine_view.load(url)

    def load_html_template_file(self, template_filepath, all_plugins_html=''):

        template_dir = os.path.dirname(os.path.abspath(template_filepath))
        template_filename = os.path.basename(template_filepath)

        j2_env = jinja2.Environment(loader=jinja2.FileSystemLoader(template_dir))
        html_str = j2_env.get_template(template_filename).render(self.html_template_vars)

        if all_plugins_html:
            html_str = html_str.replace('</body>', '%s\n\n</body>' % all_plugins_html)
            html_str = html_str.replace('</BODY>', '%s\n\n</BODY>' % all_plugins_html)

        # NOTE: cannot use .setHtml() to load the html string ... external resourses (like css and js) do not load!
        # self.web_engine_view.setHtml(html_str)

        # instead we'll write out a temp HTML file and load that
        temp_filename = 'pxlc_wew_generated_page_%s.html' % datetime.datetime.now().strftime('%Y%m%d-%H%M%S')
        temp_html_filepath = '%s/%s' % (self.session_temp_root, temp_filename)

        with open(temp_html_filepath, 'w') as out_fp:
            out_fp.write('%s\n' % html_str)

        self._load_html_file_url(temp_html_filepath)

    def run_js(self, js_str):

        self.web_engine_page.runJavaScript(js_str)

    def call_js_op(self, js_op_name, js_op_data_d):

        b64_data_str = base64.b64encode(json.dumps(js_op_data_d, sort_keys=True).encode('ascii')).decode('ascii')
        js_str_to_run = 'pweg.call_js_op("%s", "%s")' % (js_op_name, b64_data_str)
        self.run_js(js_str_to_run)

    @register_op
    def print_from_js(self, op_data):

        log_level = op_data.get('log_level', 'INFO')
        message = op_data.get('message', '???')

        print('[%s] %s' % (log_level, message))
        return {'ret_status': 'OK'}



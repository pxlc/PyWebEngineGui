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
import re
import sys
import json
import importlib


class PluginManager(object):

    CFG_TOKEN_PATTERN = r'(\${[a-zA-Z0-9_\-]+\.[a-zA-Z0-9_\-]+})' # NOTE: must escape $ character
    CFG_TOKEN_REGEX = re.compile(CFG_TOKEN_PATTERN)

    PLUGIN_HTML_TEMPLATE = '''
<!-- Plugin: {PLUGIN_NAME} (START) -->
<script language="JavaScript">
{PLUGIN_JS}
</script>
<style>
{PLUGIN_CSS}
</style>
<div id="PWEG_{PLUGIN_NAME}">
{PLUGIN_CONTENT_HTML}
</div>
<!-- Plugin: {PLUGIN_NAME} (END) -->
'''

    def __init__(self, web_engine_dialog, requested_plugins_list):

        self.wed_obj = web_engine_dialog

        self.active_plugins_root = '%s/active_plugins' % self.wed_obj.get_session_temp_root()
        os.makedirs(self.active_plugins_root)

        self.plugin_list = []
        self.plugin_info_by_name = {}
        self.plugin_instance_by_name = {}

        self.search_path_list = []
        if 'PWEG_PLUGINS_PATH' in os.environ:
            env_search_paths = [p.strip() for p in os.environ.get('PWEG_PLUGINS_PATH', '').split(os.pathsep)
                                if p.strip()]
            self.search_path_list += env_search_paths
        self.search_path_list.append('%s/plugins' % self.wed_obj.get_pweg_root())

        self.requested_plugins_list = requested_plugins_list

        for requested_plugin_name in self.requested_plugins_list:
            plugin_instance = self.request_plugin(requested_plugin_name)

    def _register_plugin_ops(self, plugin_name, op_registry):

        plugin_instance = self.get_plugin_instance(plugin_name)

        # set up callbacks here
        for attr_name in dir(plugin_instance):
            attr = getattr(plugin_instance, attr_name)
            if 'bound method' in str(attr) and hasattr(attr, '_plugin_op_name'):
                plugin_op_method = attr
                plugin_op_name = plugin_op_method._plugin_op_name.split('.')[1] \
                                    if '.' in plugin_op_method._plugin_op_name \
                                    else plugin_op_method._plugin_op_name

                full_plugin_op_name = 'Plugin|%s|%s' % (plugin_name, plugin_op_name)
                print('    adding "%s" plugin op: %s' % (plugin_name, full_plugin_op_name))
                op_registry[full_plugin_op_name] = plugin_op_method

    def register_all_plugin_ops(self, op_registry):

        for requested_plugin_name in self.requested_plugins_list:
            self._register_plugin_ops(requested_plugin_name, op_registry)

    def _convert_component_file(self, plugin_name, component_filepath, plugin_config):

        converted_lines = []
        with open(component_filepath, 'r') as fp:
            for line in fp:
                # first change all ${P} occurrences
                line = line.replace('${P}', plugin_name)
                # then replace tokens based on config
                cfg_tokens = self.CFG_TOKEN_REGEX.findall(line)
                for ctok in cfg_tokens:
                    try:
                        (scope, param) = ctok.replace('${', '').replace('}', '').split('.')
                    except:
                        self.warning('Unable to decode token "%s" in "%s" component' % (ctok, component_filepath))
                        continue
                    try:
                        replace_value = plugin_config[scope][param]
                    except:
                        self.warning('Token "%s" not defined in Plugin config (referenced in "%s" component)' %
                                     (ctok, component_filepath))
                        continue
                    line = line.replace(ctok, replace_value.replace('${P}', plugin_name))

                converted_lines.append(line.rstrip())

        return '\n'.join(converted_lines)

    def get_all_plugins_html_str(self):

        # now go through all plugins and build the html from all of the html components that each plugin needs to
        # add to the body HTML ... all of the plugin html will be added as children at the end of the <body> block

        all_plugins_html_list = []

        for plugin_name in self.plugin_list:
            p_info = self.plugin_info_by_name[plugin_name]
            if not p_info:
                self.warning('Plugin "%s" does not have any content ... not adding plugin to app.' % plugin_name)
                continue

            p_cfg = self.plugin_info_by_name[plugin_name]['config']

            p_html_str = ''
            p_css_str = ''
            p_js_str = ''

            if 'html_path' in p_info:
                p_html_str = self._convert_component_file(plugin_name, p_info['html_path'], p_cfg)
            if 'css_path' in p_info:
                p_css_str = self._convert_component_file(plugin_name, p_info['css_path'], p_cfg)
            if 'js_path' in p_info:
                p_js_str = self._convert_component_file(plugin_name, p_info['js_path'], p_cfg)

            all_plugins_html_list.append(self.PLUGIN_HTML_TEMPLATE.format(
                PLUGIN_CONTENT_HTML=p_html_str, PLUGIN_CSS=p_css_str, PLUGIN_JS=p_js_str, PLUGIN_NAME=plugin_name
            ))

        all_plugins_html = '\n'.join(all_plugins_html_list)

        # print('')
        # print(all_plugins_html)
        # print('')

        return all_plugins_html

    def load_python_plugin_code(self, plugin_name, src_plugin_path):

        active_plugin_dir_path = os.path.join(self.active_plugins_root, plugin_name)

        os.makedirs(active_plugin_dir_path)
        sys.path.insert(0, active_plugin_dir_path)

        plugin_module_name = 'PWEG%s' % plugin_name
        plugin_module_filepath = os.path.join(active_plugin_dir_path, '%s.py' % plugin_module_name)

        with open(src_plugin_path, 'r') as fp:
            src_text = fp.read()
        with open(plugin_module_filepath, 'w') as fp:
            fp.write(src_text.replace('${P}', plugin_name))

        plugin_module = importlib.import_module(plugin_module_name)

        plugin_instance = plugin_module.Plugin()
        plugin_instance._connect_to_app(plugin_name,
                                        self.wed_obj.call_js_op,
                                        self.wed_obj.debug,
                                        self.wed_obj.info,
                                        self.wed_obj.warning,
                                        self.wed_obj.error,
                                        self.wed_obj.is_modal_dialog)

        self.plugin_instance_by_name[plugin_name] = plugin_instance

        for attr_name in dir(plugin_instance):
            attr = getattr(plugin_instance, attr_name)
            if 'bound method' in str(attr) and hasattr(attr, '_plugin_op_method'):
                op_method = attr._plugin_op_method.split('.')[1] if '.' in attr._plugin_op_method \
                                                                    else attr._plugin_op_method
                op_name = '%s_%s' % (plugin_name, op_method)
                print('    adding op: %s' % op_name)
                self.add_op_handler(op_name, attr)

    def request_plugin(self, plugin_name, variation='default'):

        self.plugin_list.append(plugin_name)
        self.plugin_info_by_name[plugin_name] = {}

        # first find path to plugin in search paths
        plugin_path = ''
        for p in self.search_path_list:
            path_to_test = '%s/%s' % (p, plugin_name)
            if os.path.exists(path_to_test):
                plugin_path = path_to_test
                break

        if not plugin_path:
            self.error('Plugin "%s" not found in any of the Plugins Search Paths ... unable to load plugin.' %
                       plugin_name)
            del self.plugin_info_by_name[plugin_name]
            return

        info_pairs = [
            ('html_path', '%s/pweg_plugin.html' % plugin_path),
            ('css_path', '%s/pweg_plugin.css' % plugin_path),
            ('js_path', '%s/pweg_plugin.js' % plugin_path),
            ('py_path', '%s/pweg_plugin.py' % plugin_path),
        ]

        for (info_key, info_value) in info_pairs:
            if os.path.exists(info_value):
                self.plugin_info_by_name[plugin_name][info_key] = info_value

        # load plugin config
        config = {}
        cfg_filepath = '%s/pweg_plugin_config.json' % plugin_path

        if os.path.exists(cfg_filepath):
            with open(cfg_filepath, 'r') as fp:
                full_config = json.load(fp)
            if variation not in full_config:
                self.error('Variation "%s" not defined in config for Plugin "%s" ... unable to load plugin.' %
                        (varation, plugin_name))
                del self.plugin_info_by_name[plugin_name]
                return
            config = full_config[variation]
            config['_variation_'] = variation

        self.plugin_info_by_name[plugin_name]['config'] = config

        if 'py_path' in self.plugin_info_by_name[plugin_name]:
            self.load_python_plugin_code(plugin_name, self.plugin_info_by_name[plugin_name]['py_path'])

        return self.plugin_instance_by_name[plugin_name]

    def get_plugin_instance(self, plugin_name):

        if plugin_name not in self.plugin_instance_by_name:
            self.warning('Plugin "%s" is not in the plugin registry for this app. Unable to provide instance ' \
                         'to this plugin.')
            return None

        return self.plugin_instance_by_name[plugin_name]



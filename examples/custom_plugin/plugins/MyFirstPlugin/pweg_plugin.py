
from PyWebEngineGui.pweg import PluginBase, register_plugin_op


class Plugin(PluginBase):

    def __init__(self):

        super(Plugin, self).__init__()
        self.name = '${P}'

    @register_plugin_op
    def test_plugin_callback(self, op_data):

        # self.info(op_data.get('message', ''))
        print('Hello from ${P} callback')

    @register_plugin_op
    def roundtrip_from_js(self, op_data):

        alert_msg = op_data.get('alert_msg', '???')
        self.info('[Plugin "%s"] in roundtrip_from_js() method, got alert_msg "%s"' % (self.name, alert_msg))

        self.call_plugin_js_op('roundtrip_from_python', {'alert_msg': alert_msg})


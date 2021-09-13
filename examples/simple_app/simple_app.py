
import os
import sys

from PyWebEngineGui.pweg import WebEngineDialogBase, register_op, launch_main_app


class SimpleApp(WebEngineDialogBase):

    def __init__(self, parent=None, html_filepath='', app_title='', width=500, height=200,
                 log_level_str='INFO', log_to_shell=True):

        super(SimpleApp, self).__init__(parent=parent, app_module_path=os.path.abspath(__file__),
                                        html_filepath='', app_title=app_title, width=width, height=height,
                                        requested_plugins_list=None, override_session_log_filepath='',
                                        log_level_str=log_level_str, log_to_shell=log_to_shell)

    # --------------------------------------------------------------------------------------------------------
    # "setup_extra_template_vars()" is a REQUIRED override method
    #
    #  Establish any values for template vars in this method that you need to use in your HTML template file.
    # --------------------------------------------------------------------------------------------------------
    def setup_extra_template_vars(self):

        return {}

    @register_op
    def monkey_brains(self, op_data):
        self.call_js_op('monkey_brains', {'name': op_data.get('name', '???')})

    @register_op
    def say_hello(self, op_data):

        print('')
        print(':: [SAY_HELLO] in test_homer() method and got op_data:')
        print(op_data)
        print('')
        return {'ret_status': 'OK', 'op_name': 'say_hello', 'name': op_data.get('name', '???')}

    @register_op
    def test_homer(self, op_data):

        print('')
        print(':: [HOMER] in test_homer() method and got op_data:')
        print(op_data)
        print('')
        return {'ret_status': 'OK', 'op_name': 'test_homer'}

    @register_op
    def test_marge(self, op_data):

        print('')
        print(':: [MARGE] in test_marge() method and got op_data:')
        print(op_data)
        print('')
        return {'ret_status': 'OK', 'op_name': 'test_marge'}

    @register_op
    def test_run_js(self, op_data):

        print('')
        print(':: in test_run_js() method and got op_data:')
        print(op_data)
        print('')
        self.run_js(op_data.get('js_str'))
        return {'ret_status': 'OK', 'op_name': 'test_run_js'}

    @register_op
    def maya_make_sphere(self, op_data):

        print('')
        print(':: [MAYA] in maya_make_sphere() method and got op_data:')
        print(op_data)
        print('')
        result_d = {}
        try:
            import maya.cmds as cmds
            sphere = cmds.polySphere()
            result_d = {'ret_status': 'OK', 'op_name': 'maya_make_sphere', 'sphere': sphere}
        except:
            result_d = {'ret_status': 'WARNING', 'op_name': 'maya_make_sphere',
                        'message': 'Not running from within Maya session ... unable to make Maya sphere'}
        return result_d


if __name__ == '__main__':

    sys.exit(launch_main_app(SimpleApp, app_title='Simple App Example', width=600, height=400))



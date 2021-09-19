
import os
import sys
import importlib

from PySide2.QtWidgets import QApplication, QWidget, QMessageBox


# --------------------------------------------------------------
#  Op method registry decorator
# --------------------------------------------------------------
def register_op(op_method):

    def registered_op_method(cls_instance, op_data):
        return op_method(cls_instance, op_data)

    registered_op_method._op_name = str(op_method).split()[1]
    return registered_op_method


# --------------------------------------------------------------
#  Plugin Op method registry decorator
# --------------------------------------------------------------
def register_plugin_op(plugin_op_method):

    def registered_plugin_op_method(plugin_cls_instance, op_data):
        return plugin_op_method(plugin_cls_instance, op_data)

    registered_plugin_op_method._plugin_op_name = str(plugin_op_method).split()[1]
    return registered_plugin_op_method


def launch_main_app(custom_subclass_cls, **kwargs):

    app = QApplication([])
    # app.setApplicationDisplayName("Greetings from the other side")

    custom_app = custom_subclass_cls(**kwargs)
    custom_app.show()

    return app.exec_()


def launch_as_dialog(app_module_filepath, **kwargs):

    html_template_filepath = app_module_filepath.replace('.py', '_TEMPLATE.html')

    module_name = os.path.splitext(os.path.basename(app_module_filepath))[0]
    module_dir = os.path.dirname(app_module_filepath)

    sys.path.append(module_dir)
    app_module = importlib.import_module(module_name)

    # find the sub-class of WebEngineDialogBase
    subclass_to_instance = None

    for attr_name in dir(app_module):
        attr = getattr(app_module, attr_name)
        if 'class' in str(attr) and hasattr(attr, '__bases__'):
            base_classes = attr.__bases__
            if 'WebEngineDialogBase' in str(base_classes):
                subclass_to_instance = attr

    if subclass_to_instance:
        parent = None
        if inside_maya_dcc():
            parent = get_maya_main_window()
        elif inside_houdini_dcc():
            parent = get_houdini_main_window()  # IMPORTANT NOTE: this will hang houdini - DON'T use in houdini!
        elif inside_nuke_dcc():
            parent = get_nuke_main_window()

        kwargs['parent'] = parent
        custom_dialog = subclass_to_instance(**kwargs)
        custom_dialog.show()

        return custom_dialog
    else:
        # TODO: pop-up a confirm dialog to provide error message
        error_message_dialog('PyWebEngineGui Error', 'No WebEngineDialogBase sub-class found in app module: ' \
                                                        '"%s"' % app_module_filepath)
        return None


def error_message_dialog(dialog_window_title, dialog_error_message):

    dialog = QMessageBox()

    dialog.setIcon(QMessageBox.Warning)
    dialog.setWindowTitle(dialog_window_title)
    dialog.setText(dialog_error_message)

    dialog.setStandardButtons(QMessageBox.Ok)
    # dialog.setDefaultButton(QMessageBox.Yes)

    dialog.exec_()


# --------------------------------------------------------------
# DCC support
# --------------------------------------------------------------

def inside_maya_dcc():

    try:
        import maya.cmds as cmds
        return True
    except:
        return False


def get_maya_main_window():

    import maya.OpenMayaUI as omui
    from shiboken2 import wrapInstance
    main_window_ptr = omui.MQtUtil.mainWindow()
    main_window_widget = wrapInstance(long(main_window_ptr), QWidget)

    return main_window_widget


def inside_houdini_dcc():

    try:
        import hou
        return True
    except:
        return False


def get_houdini_main_window():

    # NOTE: ---------------------------------------------------------------------------------------------------
    # NOTE: This does not work in Houdini 18.5 even though it has the same version of PySide2 built in as Maya
    # NOTE: ... YOU CANNNOT USE THE WebEngineWindow dialog provided here in Houdini AT ALL! It hangs Houdini
    # NOTE: completely. But if it didn't hang, here is how you would attach the WebEngineWindow dialog to the
    # NOTE: Houdini main window ...
    # NOTE: ---------------------------------------------------------------------------------------------------

    # Then try to see if we are in Houdini ...
    import hou
    main_window_widget = hou.qt.mainWindow()

    return main_window_widget


def inside_nuke_dcc():

    try:
        import nuke
        return True
    except:
        return False


def get_nuke_main_window():

    app = QApplication.instance()
    for widget in app.topLevelWidgets():
        if widget.metaObject().className() == 'Foundry::UI::DockMainWindow':
            return widget



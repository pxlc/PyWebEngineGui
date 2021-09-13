
import threading
import traceback

from PyWebBrowserApp import PluginBase
from PyWebBrowserApp import register_plugin_op

# + ============================================================================
# |
# |    TaskManager plugin Python class
# |
# + ============================================================================

class TaskStatuses(object):

    NOT_STARTED = 'not_started'
    WORKING = 'working'
    COMPLETED = 'completed'
    ERRORED = 'errored'
    PAUSED = 'paused'


class LogLevels(object):

    INFO = 'info'
    DEBUG = 'debug'
    WARNING = 'warning'
    ERROR = 'error'
    CRITICAL = 'critical'


class Task(object):

    def __init__(self, task_name, validation_to_start_fn, task_execution_fn, _ui_message_driver_fn,
                 _ui_update_progress_driver_fn, _ui_task_ended_driver_fn):

        self.task_name = task_name

        self.validation_to_start_fn = validation_to_start_fn
        self.task_execution_fn = task_execution_fn

        self._ui_message_driver_fn = _ui_message_driver_fn
        self.ui_update_progress_driver_fn = _ui_update_progress_driver_fn
        self.ui_task_ended_driver_fn  = _ui_task_ended_driver_fn

        self.execution_thread = None

        self.status = TaskStatuses.NOT_STARTED

    def get_status(self):

        return self.status

    def _task_execution_wrapper(self, task_data_d, ui_message_fn, ui_progress_fn, ui_task_ended_fn,
                                LogLevels, TaskStatuses):
        try:
            self.status = self.task_execution_fn(self.task_name, task_data_d, ui_message_fn, ui_progress_fn,
                                                 ui_task_ended_fn, LogLevels, TaskStatuses)
        except:
            self.status = TaskStatuses.ERRORED

            stack_trace = traceback.format_exc()
            msg = 'Exception occurred in Task execution function - stack trace follows.\n\n%s' % stack_trace
            self.ui_message_fn(msg, LogLevels.ERROR)

    # parm signature for the ui functions are:
    # 
    #   ui_message_fn(message, message_level)
    #
    #   ui_update_progress_fn(percent_complete)
    #
    #   ui_task_ended_fn(completion_status, completion_message)
    #
    def ui_message_fn(self, message, message_level):

        self._ui_message_driver_fn(self.task_name, message, message_level)

    def ui_update_progress_fn(self, percent_complete):

        self.ui_update_progress_driver_fn(self.task_name, percent_complete)

    def ui_task_ended_fn(self, completion_status, completion_message):

        self.ui_task_ended_driver_fn(self.task_name, completion_status, completion_message)


class Plugin(PluginBase):

    def __init__(self):

        super(Plugin, self).__init__()

        self.task_by_name = {}

    def setup_task(self, task_name, validation_to_start_fn, task_execution_fn):

        # param signatures for task functions are:
        #
        #   validation_to_start_fn(task_name, task_data_d, ui_message_fn, LogLevels)
        #          |
        #          + -> returns bool, True if OK to start Task
        #
        #   task_execution_fn(task_name, task_data_d, ui_message_fn, ui_progress_fn, ui_task_ended_fn,
        #                     LogLevels, TaskStatuses)
        #
        task = Task(task_name, validation_to_start_fn, task_execution_fn,
                    self._ui_message_driver_fn, self._ui_update_progress_driver_fn,
                    self._ui_task_ended_driver_fn)

        self.task_by_name[task_name] = task

    def get_status(self, task_name):

        if task_name not in self.task_by_name:
            self.ui_message_fn('Task name "%s" not registered with TaskManager' % task_name, LogLevels.ERROR)
            return None

        task = self.task_by_name[task_name]
        return task.get_status()

    @register_plugin_op
    def get_registered_tasks(self, op_data):

        registered_task_list = sorted(self.task_by_name.keys())
        self.plugin_to_webbrowser('received_registered_tasks',
                                  {'registered_task_list': registered_task_list})

    @register_plugin_op
    def start_task(self, task_data_d):

        task_name = task_data_d.get('task_name', '')

        if task_name not in self.task_by_name:
            self._ui_message_driver_fn(task_name, 'Task name "%s" not registered with TaskManager' % task_name,
                                       LogLevels.ERROR)
            return

        task = self.task_by_name[task_name]

        if task.status in (TaskStatuses.WORKING, TaskStatuses.PAUSED):
            msg = 'Task "%s" is already running or is paused.' % task_name
            self._ui_message_driver_fn(task_name, msg, LogLevels.WARNING)
            return

        try:
            is_valid_to_start = task.validation_to_start_fn(task_name, task_data_d, task.ui_message_fn, LogLevels)
        except:
            stack_trace = traceback.format_exc()
            msg = 'Exception occurred in Task "%s" validation function - stack trace follows.\n\n%s' % \
                    (task_name, stack_trace)
            self._ui_message_driver_fn(task_name, msg, LogLevels.ERROR)
            return

        if not is_valid_to_start:
            msg = 'Task validation for start has FAILED.'
            self._ui_message_driver_fn(task_name, msg, LogLevels.ERROR)
            return

        self.plugin_to_webbrowser('ui_disable_controls', {'task_name': task_name})

        try:
            self.execution_thread = threading.Thread(target=task._task_execution_wrapper,
                                                     args=(task_data_d,
                                                           task.ui_message_fn,
                                                           task.ui_update_progress_fn,
                                                           task.ui_task_ended_fn,
                                                           LogLevels,
                                                           TaskStatuses))
            self.status = TaskStatuses.WORKING
            self.execution_thread.start()
        except:
            stack_trace = traceback.format_exc()
            msg = 'Exception occurred starting Task thread - stack trace follows.\n\n%s' % stack_trace
            self._ui_message_driver_fn(task_name, msg, LogLevels.ERROR)

            self.plugin_to_webbrowser('ui_enable_controls', {'task_name': task_name})
            return

    def _ui_message_driver_fn(self, task_name, message, message_level):

        self.plugin_to_webbrowser('ui_message',
                                  {'task_name': task_name, 'message': message, 'message_level': message_level})

    def _ui_update_progress_driver_fn(self, task_name, percent_complete):

        self.plugin_to_webbrowser('ui_update_progress',
                                  {'task_name': task_name, 'percent_complete': percent_complete})

    def _ui_task_ended_driver_fn(self, task_name, completion_status, completion_message):

        self.plugin_to_webbrowser('ui_task_ended',
                                  {'task_name': task_name, 'completion_status': completion_status,
                                   'completion_message': completion_message})




import traceback

from PySide2.QtCore import QObject, QRunnable, QThreadPool, Signal, Slot

from PyWebEngineGui.pweg import PluginBase, register_plugin_op


# + ============================================================================
# |
# |    TaskManager plugin Python class
# |
# + ============================================================================

class TaskStatuses(object):

    INACTIVE = 'inactive'  # i.e. No current TaskWorker instance
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


class TaskSignals(QObject):
    """
    Defines the signals available from a running worker thread.
    Supported signals are:
    """
    ui_message = Signal(str, str)  # message text, log level
    ui_progress = Signal(str, float)  # progress message, progress percentage (0.0 to 1.0)
    ui_task_ended = Signal(str, str)  # task ending status, completion message
    ui_process_events = Signal()


class TaskWorker(QRunnable):

    def __init__(self, task_name, validation_to_start_fn, task_execution_fn, _ui_message_driver_fn,
                 _ui_update_progress_driver_fn, _ui_task_ended_driver_fn, _ui_process_events_fn):

        super(TaskWorker, self).__init__()

        self.task_name = task_name
        self.task_data = None

        self.validation_to_start_fn = validation_to_start_fn
        self.task_execution_fn = task_execution_fn

        self.signals = TaskSignals()

        self.signals.ui_message.connect(_ui_message_driver_fn)
        self.signals.ui_progress.connect(_ui_update_progress_driver_fn)
        self.signals.ui_task_ended.connect(_ui_task_ended_driver_fn)
        self.signals.ui_process_events.connect(_ui_process_events_fn)

        # self._ui_message_driver_fn = _ui_message_driver_fn
        # self.ui_update_progress_driver_fn = _ui_update_progress_driver_fn
        # self.ui_task_ended_driver_fn  = _ui_task_ended_driver_fn

        self.status = TaskStatuses.NOT_STARTED

    def get_status(self):

        return self.status

    def _task_execution_wrapper(self, task_data_d, ui_message_fn, ui_progress_fn, ui_task_ended_fn,
                                ui_process_events_fn, LogLevels, TaskStatuses):
        try:
            self.status = self.task_execution_fn(self.task_name, task_data_d, ui_message_fn, ui_progress_fn,
                                                 ui_task_ended_fn, ui_process_events_fn,
                                                 LogLevels, TaskStatuses)
        except:
            self.status = TaskStatuses.ERRORED

            stack_trace = traceback.format_exc()
            msg = 'Exception occurred in Task execution function - stack trace follows.\n\n%s' % stack_trace
            self.ui_message_fn(msg, LogLevels.ERROR)

    # parm signature for the ui functions are:
    # 
    #   ui_message_fn(message, message_level)
    #
    #   ui_update_progress_fn(progress_message, percent_complete)
    #
    #   ui_task_ended_fn(completion_status, completion_message)
    #
    def ui_message_fn(self, message, message_level):

        self.signals.ui_message.emit(message, message_level)

    def ui_update_progress_fn(self, progress_message, percent_complete):

        self.signals.ui_progress.emit(progress_message, percent_complete)

    def ui_task_ended_fn(self, completion_status, completion_message):

        self.signals.ui_task_ended.emit(completion_status, completion_message)

    def ui_process_events_fn(self):

        self.signals.ui_process_events.emit()

    def start_task_worker(self, task_data_d, q_threadpool):

        self.status = TaskStatuses.WORKING
        self.task_data = task_data_d
        q_threadpool.start(self)

    @Slot()
    def run(self):

        self._task_execution_wrapper(self.task_data, self.ui_message_fn, self.ui_update_progress_fn,
                                     self.ui_task_ended_fn, self.ui_process_events_fn,
                                     LogLevels, TaskStatuses)


class Task(object):

    def __init__(self, task_name, validation_to_start_fn, task_execution_fn, threadpool,
                 ui_message_driver_fn, ui_update_progress_driver_fn, ui_task_ended_driver_fn,
                 ui_process_events_fn):

        self.task_name = task_name
        self.validation_to_start_fn = validation_to_start_fn
        self.task_execution_fn = task_execution_fn
        self.threadpool = threadpool

        self._ui_message_driver_fn = ui_message_driver_fn
        self._ui_update_progress_driver_fn = ui_update_progress_driver_fn
        self._ui_task_ended_driver_fn = ui_task_ended_driver_fn

        self.ui_process_events_fn = ui_process_events_fn

        self.current_task_worker = None

    def ui_message_fn(self, message, log_level):

        self._ui_message_driver_fn(self.task_name, message, log_level)

    def ui_update_progress_fn(self, progress_msg, percent_complete):

        self._ui_update_progress_driver_fn(self.task_name, progress_msg, percent_complete)

    def ui_task_ended_fn(self, completion_status, completion_message):

        self._ui_task_ended_driver_fn(self.task_name, completion_status, completion_message)

    def get_task_status(self):

        if self.current_task_worker:
            return self.current_task_worker.get_status()

        return TaskStatuses.INACTIVE

    def start_task(self, task_data_d):

        self.current_task_worker = TaskWorker(self.task_name,
                                              self.validation_to_start_fn,
                                              self.task_execution_fn,
                                              self.ui_message_fn,
                                              self.ui_update_progress_fn,
                                              self.ui_task_ended_fn,
                                              self.ui_process_events_fn)

        self.current_task_worker.start_task_worker(task_data_d, self.threadpool)


class Plugin(PluginBase):

    def __init__(self):

        super(Plugin, self).__init__()

        self.threadpool = QThreadPool()
        self.task_by_name = {}

    def setup_task(self, task_name, validation_to_start_fn, task_execution_fn):

        # param signatures for task functions are:
        #
        #   validation_to_start_fn(task_name, task_data_d, ui_message_fn, LogLevels)
        #          |
        #          + -> returns bool, True if OK to start Task
        #
        #   task_execution_fn(task_name, task_data_d, ui_message_fn, ui_progress_fn, ui_task_ended_fn,
        #                     ui_process_events_fn, LogLevels, TaskStatuses)
        #
        task = Task(task_name, validation_to_start_fn, task_execution_fn, self.threadpool,
                    self._ui_message_driver_fn, self._ui_update_progress_driver_fn,
                    self._ui_task_ended_driver_fn, self.process_events)

        self.task_by_name[task_name] = task

    def get_status(self, task_name):

        if task_name not in self.task_by_name:
            self.ui_message_fn('Task name "%s" not registered with TaskManager' % task_name, LogLevels.ERROR)
            return None

        return self.task_by_name[task_name].get_task_status()

    @register_plugin_op
    def get_registered_tasks(self, op_data):

        registered_task_list = sorted(self.task_by_name.keys())
        self.call_plugin_js_op('received_registered_tasks',
                                  {'registered_task_list': registered_task_list})

    @register_plugin_op
    def start_task(self, task_data_d):

        task_name = task_data_d.get('task_name', '')

        if task_name not in self.task_by_name:
            self._ui_message_driver_fn(task_name, 'Task name "%s" not registered with TaskManager' % task_name,
                                       LogLevels.ERROR)
            return

        task = self.task_by_name[task_name]
        task_status = task.get_task_status()

        if task_status in (TaskStatuses.WORKING, TaskStatuses.PAUSED):
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

        self.call_plugin_js_op('ui_disable_controls', {'task_name': task_name})

        try:
            task.start_task(task_data_d)  # start task execution

        except:
            stack_trace = traceback.format_exc()
            msg = 'Exception occurred starting Task thread - stack trace follows.\n\n%s' % stack_trace
            self._ui_message_driver_fn(task_name, msg, LogLevels.ERROR)

            self.call_plugin_js_op('ui_enable_controls', {'task_name': task_name})
            return

    def _ui_message_driver_fn(self, task_name, message, message_level):

        self.call_plugin_js_op('ui_message',
                                  {'task_name': task_name, 'message': message, 'message_level': message_level})

    def _ui_update_progress_driver_fn(self, task_name, progress_msg, percent_complete):

        self.call_plugin_js_op('ui_update_progress',
                                  {'task_name': task_name, 'progress_msg': progress_msg,
                                   'percent_complete': percent_complete})

    def _ui_task_ended_driver_fn(self, task_name, completion_status, completion_message):

        self.call_plugin_js_op('ui_task_ended',
                                  {'task_name': task_name, 'completion_status': completion_status,
                                   'completion_message': completion_message})



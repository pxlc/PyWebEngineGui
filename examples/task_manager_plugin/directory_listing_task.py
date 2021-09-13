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
import time


def directory_listing_task_validation(task_name, task_data, ui_message_fn, LogLevels):

    print('')
    print('>>> In directory_listing_task_validation() function')
    print('')

    folder_path = os.path.expandvars(task_data.get('folder_path', '')).strip().replace('\\', '/')

    if not folder_path or not os.path.exists(folder_path):
        message = 'Folder path "' + folder_path + '" is empty or does not exist.'
        ui_message_fn(message, LogLevels.ERROR)
        return False

    if not os.path.isdir(folder_path):
        message = 'Folder path "' + folder_path + '" is not a directory.'
        ui_message_fn(message, LogLevels.ERROR)
        return False

    return True


def directory_listing_task(task_name, task_data, ui_message_fn, ui_update_progress_fn, ui_task_ended_fn,
                           ui_process_events_fn, LogLevels, TaskStatuses):

    print('')
    print('>>> In directory_listing_task() function')
    print('')

    folder_path = os.path.expandvars(task_data.get('folder_path', '')).strip().replace('\\', '/')

    starting_msg = '\n'.join([
        '',
        '---------------------------------------------------',
        '  Starting Processing for folder path:',
        '    %s' % folder_path,
        '---------------------------------------------------',
        '',
    ])
    ui_message_fn(starting_msg, LogLevels.INFO)
    ui_update_progress_fn('progress msg', 0.0)

    item_list = sorted(os.listdir(folder_path))
    num_items = len(item_list)

    for idx, item in enumerate(item_list):
        item_path = '%s/%s' % (folder_path, item)
        ui_message_fn('>> Processing folder item: %s' % item, LogLevels.INFO)

        time.sleep(1)

        if os.path.isfile(item_path):
            ui_message_fn('   ... is a File', LogLevels.INFO)
        elif os.path.isdir(item_path):
            ui_message_fn('   ... is a Directory', LogLevels.INFO)
        else:
            ui_message_fn('   ... is a ????', LogLevels.INFO)

        percent_complete = (float(idx+1) / float(num_items)) * 100.0 + 0.5
        ui_update_progress_fn('progress msg', percent_complete)
        ui_process_events_fn()

    completion_msg = '\n'.join([
        '',
        '---------------------------------------------------',
        '  Processing of folder path:',
        '    %s' % folder_path,
        '  ... COMPLETED.',
        '---------------------------------------------------',
    ])
    ui_message_fn(completion_msg, LogLevels.INFO)
    ui_task_ended_fn(TaskStatuses.COMPLETED, 'processing completed successfully')

    return TaskStatuses.COMPLETED



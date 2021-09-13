/*
+ ==============================================================================
|
|     TaskManager plugin JavaScript
|
+ ==============================================================================
*/

function ${P}() {
    let _self = this;

    _self.registered_tasks = [];
    _self.ready = false;

    _self.override_ui_message_fn = null;
    _self.override_ui_update_progress_fn = null;
    _self.override_ui_task_ended_fn = null;

    _self.init = function()  // this is custom initialization for the specific plugin
    {
        _self.info_msg('Custom initialization for "${P}" Plugin.');
        _self._get_registered_tasks();
    };

    _self._get_registered_tasks = function() {
        _self.plugin_to_python('get_registered_tasks', {});
    };

    _self.msg_levels = {
        INFO: 'info',
        DEBUG: 'debug',
        WARNING: 'warning',
        ERROR: 'error',
        CRITICAL: 'critical',
    };

    _self.test_fn = function()
    {
        alert('Hello from ${P}');
    };

    _self.to_html_safe_text = function (str) {
        return String(str).replace(/&/g, '&amp;')
                          .replace(/</g, '&lt;')
                          .replace(/>/g, '&gt;')
                          .replace(/"/g, '&quot;');
    };

    _self.msg_log_scroll_to_end = function(task_name)
    {
        let results = document.getElementsByClassName("${P}_" + task_name + "_log");
        if (results.length) {
            for (let r=0; r < results.length; r++) {
                let msg_log_div = results[r];
                let children = msg_log_div.children;

                var total_height = 80; // add in some height to adjust for padding and such
                for (let c=0; c < children.length; c++ ) {
                    total_height = total_height + children[c].offsetHeight;
                }
                msg_log_div.scrollTop = total_height;
            }
        }
    };

    _self.start_task = function(task_name, task_data) {
        if (! _self.ready) {
            console.log('"${P}" Plugin is not in a ready state yet. Unable to start task "' + task_name + '"');
            return;
        }

        if (_self.registered_tasks.indexOf(task_name) < 0) {
            // task_name not registered
            _self.error_msg('[${P}] ERROR: Task "' + task_name + '" is not registered -- unable to start task.')
            return;
        }

        task_data.task_name = task_name;
        _self.plugin_to_python('start_task', task_data);
    };

    _self.set_progress_bar_percentage = function(task_name, percent_complete) {
        let el_results = document.getElementsByClassName("${P}_" + task_name + "_progress_fill");
        for (let c=0; c < el_results.length; c++) {
            let p_bar_div = el_results[c];
            p_bar_div.style.width = "" + percent_complete + "%";
        }
    };

    _self._set_controls_active_state = function(task_name, is_active) {
        let control_el_list = document.getElementsByClassName("${P}_" + task_name + "_control");
        for (let c=0; c < control_el_list.length; c++) {
            if (is_active) {
                if ('disabled' in control_el_list[c]) {
                    control_el_list[c].removeAttribute('disabled');
                }
            } else {
                control_el_list[c].setAttribute('disabled', 'disabled');
            }
        }
    };

    _self.ui_disable_controls = function(task_name) { _self._set_controls_active_state(task_name, false); };

    _self.ui_enable_controls = function(task_name) { _self._set_controls_active_state(task_name, true); };

    self.set_ui_message_handler = function(override_ui_message_fn) {
        // param signature for override function is (op_data) ... op_data will have key 'task_name' always
        _self.override_ui_message_fn = override_ui_message_fn;
    };

    self.set_ui_update_progress_handler = function(override_ui_update_progress_fn) {
        // param signature for override function is (op_data) ... op_data will have key 'task_name' always
        _self.override_ui_update_progress_fn = override_ui_update_progress_fn;
    };

    self.set_ui_task_ended_handler = function(override_ui_task_ended_fn) {
        // param signature for override function is (op_data) ... op_data will have key 'task_name' always
        _self.override_ui_task_ended_fn = override_ui_task_ended_fn;
    };

    // -------------------------------------------------------------------------------
    //
    //  Below are functions called from Python, so each of these only take one
    //  argument "op_data" that is a dictionary/object with any data to pass along
    //
    // -------------------------------------------------------------------------------
    _self.received_registered_tasks = function(op_data) {
        _self.registered_tasks = op_data.registered_task_list;
        _self.ready = true;

        // DEBUG
        console.log('>>> in _self.received_registerd_tasks() function - registered tasks: ' +
                    _self.registered_tasks);
    };

    _self.ui_update_progress = function(op_data) {
        if (_self.override_ui_update_progress_fn) {
            // if caller has overridden update progress function then run override
            _self.override_ui_update_progress_fn(op_data);
            return;
        }
        _self.set_progress_bar_percentage(op_data.task_name, op_data.percent_complete);
    };

    _self.ui_disable_controls = function(op_data) {
        _self.disable_controls(op_data.task_name);
    };

    _self.ui_message = function(op_data)
    {
        if (_self.override_ui_message_fn) {
            // if caller has overridden message function then run override
            _self.override_ui_message_fn(op_data);
            return;
        }

        let task_name = op_data.task_name;

        let msg = op_data.message;
        let msg_level = op_data.message_level;

        let msg_level_class = "${P}_message_" + msg_level;

        if (msg_level == "info") {
            msg_line_prefix = "[INFO]: ";
        }
        else if (msg_level == "debug") {
            msg_line_prefix = "[DEBUG]: ";
        }
        else if (msg_level == "warn") {
            msg_line_prefix = "[WARNING]: ";
        }
        else if (msg_level == "error") {
            msg_line_prefix = "[ERROR]: ";
        }
        else if (msg_level == "critical") {
            msg_line_prefix = "[CRITICAL]: ";
        }
        else {
            console.log('>>> task_name is "' + task_name + '"');
            console.log('>>> msg is "' + msg + '"');
            console.log('>>> msg_level is "' + msg_level + '"');
            msg_line_prefix = "[???]: ";
        }

        let results = document.getElementsByClassName("${P}_" + task_name + "_log");
        if (results.length == 0) {
            _self.error_msg('[${P}] ERROR: No log DIV element found for Task "' + task_name + '" ... ' +
                            'unable to log output to UI.');
            return;
        }

        let msg_lines = msg.split('\n');

        for (let c=0; c < msg_lines.length; c++) {
            // output each line
            let m_line = msg_lines[c];
            if (c == 0)
                m_line = msg_line_prefix + m_line;

            let html_str = '<span class="' + msg_level_class +'">' + _self.to_html_safe_text(m_line) +
                            "</span><br/>";

            for (let r=0; r < results.length; r++) {
                let msg_log_div = results[r];
                msg_log_div.insertAdjacentHTML('beforeend', html_str);
            }
        }

        _self.msg_log_scroll_to_end(task_name);
    };

    _self.ui_task_ended = function(op_data)
    {
        if (_self.override_ui_task_ended_fn) {
            // if caller has overridden task ended function then run override
            _self.override_ui_task_ended_fn(op_data);
            return;
        }

        let task_name = op_data.task_name;

        _self.set_progress_bar_percentage(task_name, 100.0);
        _self.msg_log_scroll_to_end(task_name);
        _self.ui_enable_controls(task_name);

        setTimeout(function() {
            alert("Task '" + task_name + "' completed with status '" + op_data.completion_status +
                  '" and message "' + op_data.completion_message + '"')
        }, 100);
    };
}

pweg.register_plugin_js(${P});



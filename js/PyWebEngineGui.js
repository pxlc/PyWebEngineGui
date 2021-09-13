
function PyWebEngineGui()
{
    let _self = this;

    _self.python_backend = null;
    _self.active_plugins = [];

    // ------------------------------------------------------
    // pweg.init() must be called on event 'DOMContentLoaded'
    // ------------------------------------------------------
    _self.init = function() {
        _self.python_backend = new Promise((resolve, reject) => {
            new QWebChannel(qt.webChannelTransport, (channel) => resolve(channel.objects.python_bridge));
        });

        // init plugins
        if (_self.active_plugins.length) {
            _self.init_plugins();
        }
    };

    _self.to_python = function(op, op_data, response_handler_fn)
    {
        const result = document.getElementById('result'); 
        const data_to_send = {'op': op, 'op_data': op_data};

        _self.python_backend.then((python_bridge) => {
            python_bridge.to_python(JSON.stringify(data_to_send), (prediction) => {
                // TODO: deterime if "prediction" is an error or not a JSON string, for now
                //       assume it will be a JSON string with return result data
                if (response_handler_fn) {
                    try {
                        const result_data = JSON.parse(prediction);
                            response_handler_fn(result_data);
                    }
                    catch(err) {
                        // TODO: output to js_log?
                        _self.error_msg('pweg.to_python() returned with error: "' + err + '"'); // can we do this?
                    }
                }
            });              
        });
    };

    _self._msg = function(message, log_level) {
        _self.to_python('print_from_js', {'message': message, 'log_level': log_level}, null);
    };

    _self.info_msg = function(message) { _self._msg(message, 'INFO'); };
    _self.error_msg = function(message) { _self._msg(message, 'ERROR'); };
    _self.warning_msg = function(message) { _self._msg(message, 'WARNING'); };
    _self.debug_msg = function(message) { _self._msg(message, 'DEBUG'); };

    _self.js_op_registry = {};
    _self.register_js_op = function(op_name, op_fn) {
        _self.js_op_registry[op_name] = op_fn;
    };

    _self.call_js_op = function(op_name, b64_data_str) {
        let decoded_str = window.atob(b64_data_str);
        let op_data = JSON.parse(decoded_str);

        if (op_name.startsWith('Plugin|')) {
            let bits = op_name.split('|');
            let plugin_name = bits[1];
            let plugin_op = bits[2];
            let plugin_instance = _self[plugin_name];
            if (!(plugin_op in plugin_instance)) {
                var msg = 'JS Plugin Op "' + plugin_op + '" does NOT exist for Plugin "' + plugin_name + '"';
                _self.error_msg(msg);
            }

            plugin_instance[plugin_op](op_data);
            return;
        }

        if (op_name.startsWith('PWEG_task_')) {
            return;
        }

        if (op_name in _self.js_op_registry) {
            var op_fn = _self.js_op_registry[op_name];
            op_fn(op_data);
        } else {
            var msg = 'JS Op "' + op_name + '" does NOT have a registered op function';
            _self.warning_msg(msg);
        }
    };

    _self.active_plugins = [];

    _self.register_plugin_js = function(plugin_function_class) {
        let plugin_instance = new plugin_function_class();
        let plugin_name = plugin_instance.constructor.name;

        plugin_instance.plugin_name = plugin_name
        plugin_instance.plugin_to_python = function(plugin_op, plugin_op_data) {
            _self.info_msg('>>> got plugin_name: "' + plugin_name + '"');
            _self.info_msg('>>> got plugin_op: "' + plugin_op + '"');
            _self._plugin_to_python(plugin_name, plugin_op, plugin_op_data);
        };

        plugin_instance.info_msg = _self.info_msg;
        plugin_instance.error_msg = _self.error_msg;
        plugin_instance.warning_msg = _self.warning_msg;
        plugin_instance.debug_msg = _self.debug_msg;

        // --------------------------------------------------------------------------------------------
        // Mechanism to reparent any HTML elements in the pwba_plugin.html file ... how this works is
        // --------------------------------------------------------------------------------------------
        //
        // (1) Any HTML elements in the pwba_plugin.html file that you want to reparent you need to add
        //     a `${P}-parent="${P}_some_element_id"` as an attribute on that element.
        //
        // (2) In your app's HTML template make sure to use the value of the above new attribute
        //     (e.g. "${P}_some_element_id"), but replacing the "${P}" part with the actual name of
        //     the plugin (e.g. "MyFirstPlugin_some_element_id"), as the ID for the element to reparent
        //     the HTML element in (1) above as a child node to be appended at the end.
        //
        plugin_instance.auto_init = function()
        {
            let plugin_name = plugin_instance.plugin_name;
            let reparent_el_list = document.querySelectorAll("[" + plugin_name + "-parent]");

            for (let c=0; c < reparent_el_list.length; c++)
            {
                let reparent_el = reparent_el_list[c];
                let target_parent_id = reparent_el.getAttribute(plugin_name + "-parent");
                let parent_el = document.getElementById(target_parent_id);

                if (parent_el) {
                    parent_el.appendChild(reparent_el.parentNode.removeChild(reparent_el));
                } else {
                    _self.error_msg('Plugin "' + plugin_name + '" is not able to reparent ' +
                                 'element with ID "' + reparent_el.id + '" ... no element with ID "' +
                                 target_parent_id + '" defined in your App\'s HTML.');
                }
            }
        };

        _self.active_plugins.push(plugin_name);

        _self[plugin_name] = plugin_instance;
    };

    _self.init_plugins = function() {
        for (let c=0; c < _self.active_plugins.length; c++) {
            let plugin_name = _self.active_plugins[c];
            let plugin_instance = _self[plugin_name];

            // run auto_init for standard Plugin mechanisms first
            if ('auto_init' in plugin_instance) {
                plugin_instance['auto_init']();
            }

            // then run init for custom Plugin initialization for the specific plugin
            if ('init' in plugin_instance) {
                plugin_instance['init']();
            }
        }
    };

    _self._plugin_to_python = function(plugin_name, op, data) {
        let full_plugin_op_spec = 'Plugin|' + plugin_name + '|' + op;
        _self.to_python(full_plugin_op_spec, data, null);
    };
}

let pweg = new PyWebEngineGui();



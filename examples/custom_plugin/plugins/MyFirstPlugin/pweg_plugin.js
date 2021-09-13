
function ${P}() {
    let _self = this;
    _self.my_id = 'blah';

    _self.show_popup = function()
    {
        let popup_div = document.getElementById("${P}_popup");
        popup_div.style.display = "block";
    };

    _self.test_fn = function()
    {
        alert('Hello from ${P}');
    };

    _self.test_callback = function()
    {
        try {
            _self.plugin_to_python("test_plugin_callback", {"message": "This is a test!"});
        } catch (err) {
            _self.error_msg('JS Error: "' + err + '"');
        }
    };

    _self.roundtrip_to_python = function()
    {
        try {
            _self.plugin_to_python(
                            "roundtrip_from_js",
                            {"alert_msg": "Alert message passed through from JS to Python and back to JS!"});
        } catch (err) {
            _self.error_msg('JS Error: "' + err + '"');
        }
    };

    _self.roundtrip_from_python = function(op_data)
    {
        alert(op_data.alert_msg);
    };
}

pweg.register_plugin_js(${P});


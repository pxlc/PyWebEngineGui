# PyWebEngineGui
Framework for using the PySide2/PyQt5 QWebEngineView widget to create HTML/CSS/JavaScript front-ends for Desktop Python apps and tools.



## Overview

The **`PyWebEngineGui`** package framework provides a way to quickly and easily create stand-alone desktop apps, or even a dialog within another PySide2/PyQt5 application, that executes its operations (and stores its data) in a Python session but that presents its UI using HTML/CSS/JavaScript through a sub-class of the **`QWebEngineView`** widget.

This framework can also be used to create dialogs (modal and non-modal) from within the [**Autodesk Maya**](https://www.autodesk.ca/en/products/maya/overview) DCC (_digital content creation_) software or in [**Foundry Nuke**](https://www.foundry.com/products/nuke) DCC software.

Being able to create the UI for dialogs or applications using web-based technologies allows for very rapid development and iteration of both the visual look and the user experience of a user interface, and results in much slicker looking and much more dynamic interfaces than traditional Qt interfaces.

This approach also opens up an enormous toolbox of JavaScript and CSS libraries that removes a huge amount of manual coding effort that might otherwise be required.



## Requirements

This framework requires the other Python packages to be available in the environment:

* `PySide2` (tested successfully only on versions `5.12.5`, in Maya 2020, and `5.15.2`) _OR_ `PyQt5` (`5.6.1`)
* `jinja2` (used for HTML templating)

Of course this parent directory containing the `PyWebEngineGui` library folder must exist in the PYTHONPATH, in order to import it.



## Compatibility

This framework integrates a copy of the open source [`QtPy` package](https://github.com/spyder-ide/qtpy) so that it can be used with either `PySide2` or `PyQt5`. However, most of the development and testing of `PyWebEngineGui` has been done using `PySide2`. This library should work across operating systems,  **_but please note_** that it has only been tested on **Windows 10**.

Below is a table of environments that were tested on and whether this framework works there or not.

#### Here are the environments tested against:

| Python version | PySide2 / PyQt5 version | _DCC_ (if applicable)       | **OS**     | Does it work here?                                           |
| -------------- | ----------------------- | --------------------------- | ---------- | ------------------------------------------------------------ |
| `3.8.2`        | PySide2 `5.15.2`        | _-- No DCC --_              | Windows 10 | **YES**                                                      |
| `3.9.7`        | PySide2 `5.15.2`        | _-- No DCC --_              | Windows 10 | **YES**                                                      |
| `2.7.11`       | PySide2 `5.12.5`        | **Autodesk Maya 2020**      | Windows 10 | **YES**                                                      |
| `2.7.16`       | PySide2 `5.12.2`        | **Foundry Nuke 12.2v3**     | Windows 10 | **YES**                                                      |
| `2.7.13`       | PyQt5 `5.6`             | **Foundry Katana 4.0v5**    | Windows 10 | _NO_ - HTML UI does display mostly, but the library's required JavaScript fails due to JavaScript strict mode enforced by the Katana PyQt5 build, so functionality breaks and the library effectively **_does not work_** here. |
| _`3.9.5`_      | PySide2 _`5.15.2`_      | _-- No DCC --_              | Windows 10 | _NO_ - does not work                                         |
| _`2.7.15`_     | PySide2 _`5.12.6`_      | **SideFX Houdini 18.5.462** | Windows 10 | _NO_ - does not work (_totally hangs houdini_)               |
| _`2.7.15`_     | PySide2 _`5.12.6`_      | **SideFX Houdini 18.5.633** | Windows 10 | _NO_ - does not work (_totally hangs houdini_)               |



So, to summarize, the `PyWebEngineGui` framework library can be used successfully when run command line with Python 3.8+ (except, strangely, not Python 3.9.5) and PySide2 5.12.2+ or PyQt5 5.6+. It can also be used successfully from within Autodesk Maya 2020 (sorry haven't tested in any other Maya versions yet) and Foundry Nuke 12.2v3.

DO NOT use this with SideFX Houdini ... use of the `QWebEngineView` widget seems to just hang Houdini completely. As well this library doesn't really work in Foundry Katana, so don't use it there either.



## Documentation

Outside of this README there is no further documentation _yet_ for this framework library. For now please see the examples provided in the `examples` folder.



## Examples


Here is how you can run the examples from the command line:

```bash
> # assume you have cd'ed into your copy of the PyWebEngineGui local repo folder
> # (and assume that PySide2 and jinja2 are available to your Python environemnt
> # and that this local PyWebEngineGui repo folder can also be found in PYTHONPATH)
>
> python3 ./examples/simple_app/simple_app.py
>
> python3 ./examples/custom_plugin/custom_plugin_app.py
>
> python3 ./examples/launcher_app/launcher_app.py
>
> python3 ./examples/task_manager_plugin/task_manager_plugin_app.py
>
```



#### The Examples

| Example app                      | Description                                                  |
| -------------------------------- | ------------------------------------------------------------ |
| **`simple_app.py`**              | Simple app that uses Bootstrap library in its HTML front end and demonstrates calling Python functionality, through registered Python op methods from JavaScript and round-tripping back to JavaScript (either through return data handling or by Python calling JavaScript functionality through registered JS ops). **NOTE:** this app also has a button that will create a sphere in Autodesk Maya, if the app is run as a dialog from within Maya. |
| **`custom_plugin_app.py`**       | This app demonstrates how you can write your own `PyWebEngineGui` plugin to add Python and JavaScript functionality, as well as add HTML elements into an existing app front end. |
| **`launcher_app.py`**            | This app shows how you can create an app/tool launcher with sets of tool buttons organized by project. |
| **`task_manager_plugin_app.py`** | The `PyWebEngineGui` framework comes with one built-in plugin, called the **`TaskManager`** plugin. You can include this plugin in your app in order to execute long running tasks that can communicate back to the HTML front end during its execution in order to update a progress bar and provide user feedback. |



#### Running the examples as a Dialog in another PySide2 app

From within the code of another PySide2 app (this includes running from within Autodesk Maya), you simply import the framework and run the following:

```python
from PyWebEngineGui import pweg
instantiation_params = {'width': 600, 'height': 480}
pweg.launch_as_dialog('${PATH_TO_PYWEBENGINEGUI_DIR}/examples/simple_app/simple_app.py',
                      **instantiation_params)
```



#### Running as a Modal Dialog

The base **`WebEngineDialogBase`** class that all of these app example classes are derived from has a parameter to its `__init__` method named `is_modal_dialog` that defaults to `False`. In order to run your app as a Modal Dialog, you must ensure your sub-class passes in `is_modal_dialog=True` as a parameter when running the `__init__` of the base class.

The `TaskManagerPluginApp` sub-class of the `task_manager_plugin_app.py` example has its own `is_modal_dialog` param that defaults to `True`, and that is passed along to the `WebEngineDialogBase` base class. So you can run that example directly as a modal dialog from within another PySide2 app.



<br>

**[end]**

PyTest Web UI
-------------

[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

A web app for controlling PyTest interactively. With it, you can explore your
test hierarchy (test packages/modules/classes/methods etc.), run tests at the
click of a button and see the results presented in your web browser.

![Screenshot](https://raw.githubusercontent.com/ryanc414/pytest_commander/master/img/screenshot1.png)

Features
========

- Run tests by group (module, class etc.) or individually.
- Clear pass/fail labelling so you can dig down and find what failed quickly,
  instead of having to scroll up through many screens of terminal output.
- Test files and dependencies are reloaded every time so you can run, tweak your
  code, then run again in a fast iteration cycle.
- Runs on any modern OS and browser (tested on Win10, macOS and Ubuntu with
  Chrome, Firefox and Safari). IE is not supported.
- Automatically start and stop docker services while running if specified in a
  `docker-compose.yml` file in the root test directory.
- Tests are run in separate processes and reloaded for each invocation, allowing
  tests to be tweaked and re-run without restarting the main process.

Prerequisites
=============

- Requires Python3.6+ and pip.

Quickstart
==========

Install and get started running your own PyTest tests:

```
pip install pytest-commander
pytest_commander /path/to/your/tests
```

I recommend installing into an activated
[virtual environment](https://docs.python.org/3/tutorial/venv.html). You will
want to make sure that all additional dependencies required to run your tests
are installed into the same virtual environment.

When you run with default options, the web app to browse and run tests should be
opened automatically in your default browser. To view full docs for the
command-line parameters, run `pytest_commander --help`.

Build from source
=================

Alternatively you may build from source. In addition to the prerequisites above,
you must ensure you have installed [pipenv](https://pipenv.pypa.io/en/latest/)
and [npm](https://www.npmjs.com/get-npm).

```
git clone https://github.com/ryanc414/pytest_commander.git
cd pytest_commander
python build.py
python test.py
```

You may then install the local directory into an activated virual environment,
along with other dependencies installed to run your tests:

```
pip install .
pytest_commander /path/to/your/tests
```

Happy testing!
PyTest Web UI
-------------

[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

A web app for controlling PyTest interactively. With it, you can explore your
test hierarchy (test packages/modules/classes/methods etc.), run tests at the
click of a button and see the results presented in your web browser.

Features
========

- Run tests by group (module, class etc.) or individually.
- Clear pass/fail labelling so you can dig down and find what failed quickly,
  instead of having to scroll up through many screens of terminal output.
- Test files and dependencies are reloaded every time so you can run, tweak your
  code, then run again in a fast iteration cycle.
- Runs on any modern OS (tested on Win10, macOS and Ubuntu)

Prerequisites
=============

- Requires Python3.6+ and pip.

Quickstart
==========

Install and get started running your own PyTest tests:

```
pip install pytest_web_ui
pytest_web_ui /path/to/your/tests
```

I recommend installing into an activated
[virtual environment](https://docs.python.org/3/tutorial/venv.html). You will
want to make sure that all additional dependencies required to run your tests
are installed into the same virtual environment.

Build from source
=================

Alternatively you may build from source. In addition to the prerequisites above,
you must ensure you have installed [pipenv](https://pipenv.pypa.io/en/latest/)
and [npm](https://www.npmjs.com/get-npm).

```
git clone https://github.com/ryanc414/pytest_web_ui.git
cd pytest_web_ui
python build.py
python test.py
```

You may then install the local directory into an activated virual environment:

```
pip install .
# Now install other dependencies needed to run your tests.
pytest_web_ui /path/to/your/tests
```

Happy testing!
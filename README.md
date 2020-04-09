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

How to use
==========

Currently, you must install from source. Start by cloning this repo:

```
git clone https://github.com/ryanc414/pytest_web_ui.git
```

Secondly, you must compile the typescript code so that it can run in your
browser:

```
cd pytest_web_ui/pytest_web_ui
npm install
npm run build
```

Next, ensure all python dependencies are installed using
[pipenv](https://pipenv.pypa.io/en/latest/):

```
cd ..
pipenv install
# Install any additional dependencies required to run your tests.
```

Finally, start the pytest web UI server process and navigate your browser
to http://localhost:5000

```
pipenv run python -m pytest_ui_server /path/to/your/tests
```

Happy testing!
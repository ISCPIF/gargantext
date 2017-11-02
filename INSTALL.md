# Gargantext installation and dev environment

## TL;DR

You need `pipenv` and an up-to-date version of `pip`. To install and run:

    $ pipenv install
    $ pipenv run ./manage runserver


## Requirements

### Up-to-date pip

On Debian-like distros, `pip` is not installed by default, if you didn't do it
already:

    $ sudo apt install python3-pip

Pipenv (see below) needs an up-to-date version of pip, on a Debian-like just
`apt upgrade`, otherwise upgrade it like so:

    $ pip install pip --user --upgrade

### Pipenv

You will need [pipenv][1] to easily get dependencies of Gargantext.
It handles packages and takes care of the virtualenv and environment variables.

There are various ways to install `pipenv`, see its [documentation][2] for more
insights. Here is the straightforward way:

    $ pip install pipenv --user

[1]: https://github.com/kennethreitz/pipenv
[2]: https://docs.pipenv.org/


## Installation

To bootstrap Gargantext environment just cd into your local Gargantext repo and
do:

    $ pipenv install

If everything is going well, you now have a clean virtualenv with every
packages you need to run Gargantext. Here is how to get the path of the
virtualenv directory pipenv just created:

    $ pipenv --venv

You can now run any command by prefixing it with `pipenv run` or by first
entering the virtualenv with `pipenv shell`. To run Gargantext django backend
test server you can do:

    $ pipenv run ./manage.py runserver

But also:

    $ pipenv shell
    $ ./manage.py runserver
    $ ... continue in your virtualenv ...


## Customize dev environment

To install specific packages without messing with dependencies, just use pip.
For example, to install ipython or bpython shells locally:

    $ pip install ipython
    $ pip install bpython

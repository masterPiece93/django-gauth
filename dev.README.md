# Google Auth <sup>[ Django ]</sup> <sup><small><b>< Developer Version ></b><small></sup>


### Install pipx

- [Pipx : Installation : Linux](https://docs.google.com/document/d/16jzSA98KBekGqaVJDZtr_7mC_CooHe49byiYcvixW0g/edit?tab=t.0#heading=h.ymbho9y6133c)


- - post installation
    - ```sh
        pipx ensurepath
        ```

### Install PDM

```sh
pipx install --suffix "@djangoGauth" pdm --python python3.12

# If Alias Required :
# pipx install <package_name> --alias <desired_alias> --python python3.12
```

- Ensure PDM installation
    ```sh
    pipx list
    ```
    - you must see the name `pdm@djangoGauth` in the list .

### Initialize PDM

**initialize** 
```sh
pdm@djangoGauth init
```
- now it will ask interactive options , since the information already exists in pyproject.toml file , please refer it .
    - in options with no default value , skip
    - in options with default value , enter valid value by reffering .toml file


**Add groups** ( if pdm.lock file doesn't exists )
-
```sh
pdm@djangoGauth lock --group dev --group lint
```

**Install dependencies**
```sh
pdm@djangoGauth install -G <option>
```

- All Dependencies
    ```sh
    pdm@djangoGauth install -G :all

    # if you wish to install all dependencies
    ```

- Linting Dependencies
    ```sh
    pdm@djangoGauth install -G lint

    # if you wish to install only lint related dependencies
    ```

- Development Dependencies
    ```sh
    pdm@djangoGauth install -G dev

    # if you wish to install only lint related dependencies
    ```

**Sync PDM** ( if pdm.lock exists )
```sh
pdm@djangoGauth sync
```

```sh
# list all installed packages
pdm@djangoGauth list
```

### Create Build / Package

generate build
```sh
pdm@djangoGauth build
```

verify build
```sh
pdm@djangoGauth check_build
```

> **NOTE** : before generating build , do perform necessary code linting and validation steps .


### Code Checks

```sh
pdm@djangoGauth mypy

# show the typing issues
```

```sh
pdm@djangoGauth lint

# show the linting errors
```

```sh
pdm@djangoGauth format

# perform formatting on code
```

```sh
pdm@djangoGauth fix

# fix linting issues 
```

## List the Contents of Wheel File
```sh
import pprint
from zipfile import ZipFile

path = 'pep8-1.7.0-py2.py3-none-any.whl'
names = ZipFile(path).namelist()
pprint.pprint(names)
```

## Verify the Dist

**Install the tool :**
```sh
pip install check-wheel-contents
```

**Use :**
```sh
check-wheel-contents dist/
```

## Install Local dist
install a dist you just created

```sh
pip install -e .
# can be used when you have a single dist/ file
```
OR
```sh
pip install /path/to/your/dist/file.whl
# can be used when you have multiple dist/ files with different version
```

## Tools

`mypy`
```sh
mypy src/
```

## DevPlatform


```sh
pdm@djangoGauth build
```

Personally Managing a venv :

- ```sh
    # enter devPlatform
    cd devPlatform/
    ```

- ```sh
    # Create a virtual environment 
    python3 -m venv venv
    ```

- ```sh
    # Activate Virtual Environment
    source venv/bin/activate
    ```

- ```sh
    # Install Requirements
    pip install -r requirements/requirements.txt
    ```

- ```sh
    # install `django_gauth` package
    pip install -e ../.
    ```
    - post this , whatever changes you will make in the local package , they'll be automatically reflected in here .

- ```sh
    # start server on localhost:8000
    python3 manage.py runserver localhost:8000
    ```

Using Make :

- ```sh
    cd devPlatform/
    ```

- first time use
    ```sh
    make all
    ```

- consecutive use
    ```sh
    make runserver
    ```

## Testing

all tests reside in `tests/` folder at root level

- create test virtualenvironment
    ```sh
    python3 -m venv test-venv
    ```
    ```sh
    activate test-venv/bin/activate
    ```
- install test requirements 
    ```sh
    pip install -r tests/requirements.txt
    ```
- run tests
    ```sh
    python3 runtests.py
    ```

There are certain automation tests , residing in same `tests` directory .
They are switched-off by default .
If you want to run them , then you can **turn on** the automation tests , setting `AUTOMATION='1'`
If you only wish to run only the unit tests , then you can **turn off** the automation tests , setting `AUTOMATION='0'` or simply unsetting the `AUTOMATION` env variable.

- setting
    ```
    # linux
    export AUTOMATION="0"
    ```
- un-setting
    ```
    # linux
    unset AUTOMATION
    ```

During the test runs , the Django TestRunner is set up .
It creates a mock django project , to run your reusable app in & hence run your tests .

The settings are setup partly using the devPlatform and partly setting manully .
    - find these in `runtests.py` file

Test Environment:

- Certain settings are loaded from `.env` file .
- you can specify your own test environment . Use `ENV_PATH` variable .
    - export it in your teminal/cmd , and give it a absolute path to a `.env` file .
- you must use the `tests/.env.template` file and create a new `.env.test` file from it and populate desired values .

## Documentation

running mkdocs :

```sh
mkdocs serve
```

## Important Points

* always use pypi's [official classifier's](https://pypi.org/classifiers/) list to find classifiers for your python pacakge .
    - NOTE : invalid classifiers will raise errors at the time of publishing package to pypi

* use [validate-pyproject](https://pypi.org/project/validate-pyproject/) python utility for validating your `pyproject.toml` files during development , before publishing to pypi . 

* pdm dependency multi range adjusted addition
```sh
pdm add "package_name; environment_marker"
```
```sh
pdm add "some-package; python_version >= '3.8' and python_version < '3.12'" "another-package; python_version >= '3.9' or python_version < '3.7'"
```
```sh
pdm add "my-library==1.0.0; python_version < '3.9'" "my-library==2.0.0; python_version >= '3.9'"
```
For Example :
    * ```sh
    pdm@djangoGauth add "Django>=3.1; python_version>='3.9' and python_version<'3.11'" "Django>=4.2; python_version>='3.9'"
    ```
    * ```sh
    pdm add "colorama; sys_platform == 'win32' and python_version < '3.9'"
    ```

* allow nox to use pyenv installed python versions

```sh
pyenv global 3.8.12 3.9.5 3.10.2
```

* Django Compatibility Chart
```
Django 6.0 (under development): Supports Python 3.12, 3.13, and 3.14.
Django 5.2.x series: The last series to support Python 3.10 and 3.11.
Django 5.1: Supports Python 3.10, 3.11, 3.12, and 3.13.
Django 5.0: Compatible with Python versions 3.10, 3.11, and 3.12.
Django 4.2: Supports Python 3.8, 3.9, 3.10, 3.11, and 3.12 (as of 4.2.8). This is an LTS (Long Term Support) release. 
Django 4.0: Supports Python 3.8, 3.9, and 3.10.
```
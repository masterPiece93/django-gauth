# Google Auth <sup>[ Django ]<sup>


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


**non-interactive initialize**
```sh
pdm init --non-interactive --python 3.11 --lib --backend pdm-backend
```

**Add groups** ( if pdm.lock file doesn't exists )
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
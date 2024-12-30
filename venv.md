Well, Pyhton is not my primary language, so this note is to recap how to use venv when needed.

**Creating a virtual env**

```shell
python -m venv .venv
```

**Activating it**

```shell
# windows
.\.venv\Scripts\Activate.ps1
```

**Generating the requirements.txt**

```shell
pip freeze > requirements.txt
```


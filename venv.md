# Using a Virtual Environment with Python

### Introduction

A virtual environment (venv) is a self-contained directory that contains a Python interpreter, libraries, and other
dependencies. This note provides a quick guide to creating, activating, and using a venv when working with Python
projects.

### Creating a Virtual Environment

To create a new venv, run the following command in your terminal or command prompt:
```bash
python -m venv .venv
```
This will create a new directory called `.venv` containing a self-contained Python environment.

### Activating the Virtual Environment

To start using the virtual environment, you need to activate it. The steps are slightly different depending on your
operating system:

**Windows:**

```shell
# Activate the venv
.\.venv\Scripts\Activate.ps1

# Deactivate the venv when you're done
deactivate
```

**macOS/Linux:**

```bash
# Activate the venv
source .venv/bin/activate

# Deactivate the venv when you're done
deactivate
```

### Generating `requirements.txt`

After installing your project's dependencies, you can generate a `requirements.txt` file to keep track of them:
```bash
pip freeze > requirements.txt
```
This will create a new file called `requirements.txt` containing all the installed packages and their versions.

### Installing Requirements from `requirements.txt`

To install the listed packages from your `requirements.txt` file, run:
```bash
pip install -r requirements.txt
```
This command tells pip to read the `requirements.txt` file and install all listed packages. Make sure you're in the
correct directory where your `requirements.txt` file is located.

### Tips

* Always activate the venv before installing dependencies or running scripts.
* Use a consistent naming convention for your virtual environments (e.g., `.venv`).
* If you encounter issues with package versions, try specifying them in the `requirements.txt` file using
`==version-number`.
* Consider installing packages within a virtual environment to keep project dependencies isolated.

By following these steps and tips, you'll be well on your way
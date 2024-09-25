# Backend repository for the project "The Switcher Game"
## Installation and configuration
To run the project you must follow the following steps:
### Configuring the environment
1. Install Python if you don't have it installed on your machine. You can do this by running the following command:
```bash
sudo apt-get install python3
```
2. Next, install pip, the Python package manager, by running the following command:
```bash
sudo apt-get install python3-pip
```
3. Install the virtualenv package by running the following command:
```bash
sudo apt-get install python3-venv
```
Once you have installed all the dependencies, you can continue with the next steps to run the project.
--- 
#### Creating a virtual environment
To run the project you must create a virtual environment. To do this, follow the following steps:

1. Create a directory where you want to store the virtual environment. You can do this by running the following command:
```bash
mkdir <directory_name>
```
2. Change to the directory you just created by running the following command:
```bash
cd <directory_name>
```

3. Create the virtual environment by running the following command:
```bash
python3 -m venv <virtual_environment_name>
```

4. Activate the virtual environment by running the following command:
```bash
source <virtual_environment_name>/bin/activate
```
You will know that the virtual environment is activated when you see the name of the virtual environment in parentheses at the beginning of the command line.

Every time you want to run the project you must activate the virtual environment, repeating step 4.

- To deactivate the virtual environment, run the following command:
```bash
deactivate
```
---

### Installing requeriments
1. Clone the repository by running the following command:
```bash
git clone https://github.com/IngSoft1-MANEJA/backend.git
```
2. Next, you must to activate the virtual environment. To do this, follow the steps in the "Creating a virtual environment" section.

3. Once the virtual environment is activated, change to the directory where the repository was cloned by running the following command:
```bash
cd path/to/backend
```
4. Install the project dependencies by running the following command:
```bash
pip install -r requirements.txt
```

If you have any problems with the installation, you can try to install the dependencies one by one by running the following command:
```bash
pip install <dependency_name>
```
Once you have installed all the dependencies, you can continue with the next steps to run the project.

---
## Running the project
To run the project in your local machine, follow the following steps:
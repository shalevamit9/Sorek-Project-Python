# Sorek-Python-Project

## Common setup

Clone the repo and install the dependencies.

```bash
git clone https://git.pblm.tech/shalevamit9/sorek-project-python
cd sorek-project-python
```

```bash
pip install -r requirements.txt
```

## Environment Configuration
As you open IDE run the following commands:

for development:

```bash
set FLASK_ENV=development
set FLASK_APP=run.py
```

## RUN
Run the application with the following command

```bash
flask run
```

## Usage
To start the algorithm a HTTP POST request needs to be sent to:

```bash
http://localhost:5000/start
```

The request contains a body in the next format:

```json
{ 
    "year": 2021,
    "target": 151700000
}
```

• year field is the year to create a plan for.<br>
• target field is the production amount to achieve in the plan.
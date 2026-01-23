VENV=.venv
PYTHON=$(VENV)/Scripts/python
PIP=$(VENV)/Scripts/pip

install:
	conda activate sanctum
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements.txt

run:
	uvicorn app.main:app --reload

freeze:
	$(PIP) freeze > requirements.txt

clean:
	rm -rf .venv __pycache__

# db-check:
# 	$(PYTHON) -c "from app.database import engine; print('DB Connected!')"

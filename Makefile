export PYTHONPATH := src

.PHONY: install test train eval api app docker

install:
	pip install -r requirements.txt

test:
	python -m pytest -q

train:
	python -c "from repro360.model import train; import json; print(json.dumps(train(), indent=2))"

eval:
	python -m repro360.evidence_eval

api:
	uvicorn repro360.api:app --reload --port 8000

app:
	streamlit run app/streamlit_app.py

docker:
	docker compose up --build

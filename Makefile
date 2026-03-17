.PHONY: install run docker-build docker-run clean

install:
	pip install --no-cache-dir -r requirements.txt

run:
	python evaluate.py \
		--source data/source.txt \
		--translation data/translation.txt \
		--output reports/report.json \
		--lang-pair en-es

docker-build:
	docker build -t evaluator .

docker-run:
	docker run --rm evaluator

clean:
	rm -rf reports/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -name "*.pyc" -delete
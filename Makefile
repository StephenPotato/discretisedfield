PROJECT=discretisedfield
IPYNBPATH=docs/ipynb/*.ipynb
CODECOVTOKEN=a96f2545-67ea-442e-a1b6-fdebc595cf52
PYTHON?=python3

test:
	$(PYTHON) -m pytest

test-test:
	$(PYTHON) -c "import discretisedfield as d; d.test()"

test-coverage:
	$(PYTHON) -m pytest --cov=$(PROJECT) --cov-config .coveragerc

test-ipynb:
	$(PYTHON) -m pytest --nbval $(IPYNBPATH)

test-docs:
	$(PYTHON) -m pytest --doctest-modules --ignore=$(PROJECT)/tests $(PROJECT)

test-all: test-test test-coverage test-ipynb test-docs

upload-coverage: SHELL:=/bin/bash
upload-coverage:
	bash <(curl -s https://codecov.io/bash) -t $(CODECOVTOKEN)

travis-build: SHELL:=/bin/bash
travis-build:
	docker build -t dockertestimage1 -f docker/Dockerfile1 .
	docker run -e ci_env -ti -d --name testcontainer1 dockertestimage1
	docker exec testcontainer1 make test-test
	docker stop testcontainer1
	docker rm testcontainer1

	ci_env=`bash <(curl -s https://codecov.io/env)`
	docker build -t dockertestimage2 -f docker/Dockerfile2 .
	docker run -e ci_env -ti -d --name testcontainer2 dockertestimage2
	docker exec testcontainer2 make test-all
	docker exec testcontainer2 make upload-coverage
	docker stop testcontainer2
	docker rm testcontainer2

test-docker:
	make travis-build

build-dists:
	rm -rf dist/
	$(PYTHON) setup.py sdist
	$(PYTHON) setup.py bdist_wheel

release: build-dists
	twine upload dist/*

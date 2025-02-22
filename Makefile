.ONESHELL:
SHELL = /home/linuxbrew/.linuxbrew/bin/zsh
CONDA_ACTIVATE = source $$(conda info --base)/etc/profile.d/conda.sh ; conda activate ; conda activate

# Default target: activate the environment
default: build start

build:
	sudo bundle install
	conda env create -f environment.yml || true
	$(CONDA_ACTIVATE) health-and-beauty-lab
	pip install --upgrade pip
	pip install -r requirements.txt

start:
	bundle exec jekyll serve --livereload

deploy:
	JEKYLL_ENV=production bundle exec jekyll build

translate: 
	$(CONDA_ACTIVATE) health-and-beauty-lab
	python _translate.py

prune:
	conda env update --prune -f environment.yml

.PHONY: build start deploy translate prune
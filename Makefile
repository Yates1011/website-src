SHELL := /bin/bash

.PHONY: help
help: ## Show this help
	@grep -E '^[0-9a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-10s\033[0m %s\n", $$1, $$2}'

.PHONY: update
update: ## Build the site live into /var/www/html (publishes immediately)
	python3 build.py

.PHONY: serve
serve: ## Build into ./out and preview at http://localhost:8000
	python3 serve.py

.PHONY: publish
publish: update ## Build live, then push source to GitHub
	git push

.PHONY: clean
clean: ## Remove the local preview build (./out)
	rm -rf out

default: help

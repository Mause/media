# https://just.systems

default:
	just --list

pull-config:
	heroku config --app=rarbg-interface --shell > .env

snapshot:
	pytest --snapshot-update
	cd app && yarn generate:static

typecheck:
	mypy rarbg_local
	cd app && yarn tsc

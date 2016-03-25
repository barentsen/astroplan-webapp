devserver:
	python start-devserver.py

local:
	heroku local

deploy:
	git push heroku master

setup:
	heroku apps:create astroplanapp

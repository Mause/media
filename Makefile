all: build

watch:
	rm -f rarbg_local/static/gen/streaming.js
	./node_modules/.bin/watchify -p [ tsify --module es5 --inlineSourceMaps ] \
		--debug
		-t browserify-css \
		rarbg_local/static/streaming.tsx \
		-o rarbg_local/static/gen/streaming.js

build:
	rm -f rarbg_local/static/gen/streaming.js
	./node_modules/.bin/browserify -p [ tsify --module es5 --inlineSourceMaps ] \
		--debug
		-t browserify-css \
		rarbg_local/static/streaming.tsx \
		-o rarbg_local/static/gen/streaming.js

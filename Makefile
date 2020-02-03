all: build

INPUT = rarbg_local/static/streaming.tsx
OUTPUT = rarbg_local/static/gen/streaming.js

clean:
	rm -f $(OUTPUT)

watch: clean
	./node_modules/.bin/watchify -p [ tsify --module es5 --inlineSourceMaps ] \
		--debug \
		-t browserify-css \
		-p [ browserify-livereload --host 127.0.0.1 --port 1337 ] \
		$(INPUT) \
		-o $(OUTPUT)

build: clean
	./node_modules/.bin/browserify -p [ tsify --module es5 --inlineSourceMaps ] \
		--debug \
		-t browserify-css \
		$(INPUT) \
		-o $(OUTPUT)

prod: clean
	./node_modules/.bin/browserify -p [ tsify --module es5 ] \
		-t browserify-css \
		-g [ envify --NODE_ENV production --HEROKU_SLUG_COMMIT $(HEROKU_SLUG_COMMIT) ] \
		-g uglifyify \
		$(INPUT) \
		| ./node_modules/.bin/terser --compress --mangle > $(OUTPUT)

	cd app && yarn && yarn test && yarn build

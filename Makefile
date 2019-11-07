PLUGIN_VERSION=0.0.2
PLUGIN_ID=alter-hive-string-to-varchar

plugin:
	cat plugin.json|json_pp > /dev/null
	rm -rf dist
	mkdir dist
	zip --exclude "*.pyc" -r dist/dss-plugin-${PLUGIN_ID}-${PLUGIN_VERSION}.zip plugin.json custom-recipes python-lib python-runnables

clean:
	rm -rf dist


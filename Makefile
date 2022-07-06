doc:
	cd docs && make html

wheel:
	rm -rf build
	rm -rf dist
	python setup.py sdist bdist_wheel

upload:
	twine upload dist/*

clean:
	rm -rf examples/_tmp
	make soft_clean

soft_clean:
	rm -rf docs/source/_graphs docs/source/_data.rst

example:
	cd examples && python create_graphs.py && python create_rst.py
	mv examples/_data.rst docs/source
# 	cd docs/source/_graphs && ls geomstats*.svg | xargs -n 1 xdg-open

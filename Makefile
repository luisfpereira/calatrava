doc:
	cd docs && make html

wheel:
	rm -rf build
	rm -rf dist
	python setup.py sdist bdist_wheel

upload:
	twine upload dist/*

clean:
# 	rm -rf docs/examples/_tmp
	rm -rf docs/_build
	make soft_clean

soft_clean:
	rm -rf docs/source/_graphs docs/source/_data.rst

example:
	cd docs/examples && python create_graphs.py && python create_rst.py
# 	cd docs/source/_graphs && ls geomstats*.svg | xargs -n 1 xdg-open

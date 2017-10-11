# You can set these variables from the command line.
SPHINXOPTS    = -W
SPHINXBUILD   = sphinx-build
PAPER         =
BUILDDIR      = _build
STATICDIR     = _static

# Internal variables.
ALLSPHINXOPTS   = -d $(BUILDDIR)/doctrees $(SPHINXOPTS) .

.PHONY: clean
clean:
	rm -rf $(BUILDDIR)
	rm examples/*.html | true

.PHONY: doc-examples
doc-examples:
	./gen_html.py

.PHONY: html
html: clean doc-examples
	mkdir -p $(STATICDIR)
	$(SPHINXBUILD) -b html $(ALLSPHINXOPTS) $(BUILDDIR)/html
	@echo
	@echo "Build finished. open file://`pwd`/_build/html/index.html"

.PHONY: linkcheck
linkcheck:
	mkdir -p $(STATICDIR)
	$(SPHINXBUILD) -b linkcheck $(ALLSPHINXOPTS) $(BUILDDIR)/linkcheck
	@echo
	@echo "Link check complete; look for any errors in the above output " \
	      "or in $(BUILDDIR)/linkcheck/output.txt."

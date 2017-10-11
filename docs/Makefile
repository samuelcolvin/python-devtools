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
	@( echo '<pre class="ansi2html-content">'; \
	PY_DEVTOOLS_HIGHLIGHT=true python examples/1_input.py | ansi2html -p; \
	echo '</pre>' ) > examples/1_output.html
	@( echo '<pre class="ansi2html-content">'; \
	PY_DEVTOOLS_HIGHLIGHT=true python examples/2_input.py | ansi2html -p; \
	echo '</pre>' ) > examples/2_output.html

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

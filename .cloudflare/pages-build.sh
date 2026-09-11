#!/bin/sh
set -eu

rm -rf _site
mkdir _site

cp index.html 404.html site-refresh.css blog.css lang.js logo.png ogp.png ogp-v3.png robots.txt sitemap.xml llms.txt _site/
cp -R assets blog post en _site/
for d in $(python3 _tools/build_redirects.py --list-top); do if [ -d "$d" ] && [ ! -e "_site/$d" ]; then cp -R "$d" _site/; fi; done
touch _site/.nojekyll

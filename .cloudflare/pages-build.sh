#!/bin/sh
set -eu

rm -rf _site
mkdir _site

cp index.html 404.html site-refresh.css blog.css logo.png ogp.png ogp-v3.png robots.txt sitemap.xml llms.txt _site/
cp -R assets blog post _site/
touch _site/.nojekyll

#!/bin/bash

version=$1

# Create git tag so PBR can get the version
git tag -a "$version" -m "Release $version"

# Install/Update python3 build module
python3 -m pip install --upgrade build

# Build
python3 -m build

# Publish on PyPI
twine upload dist/*

# Commit ChangeLog and retag (so the tag points to the ChangeLog commit)
git add ChangeLog
git commit -m "Release $version"
git tag -d $version
git tag -a "$version" -m "Release $version"

# Push to remote repo
git push --follow-tags

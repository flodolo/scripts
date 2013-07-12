#! /usr/bin/env bash

# Script used to run Meld, comparison betweeb trunk and stage
meld svn/mozilla.com/trunk/locales svn/mozilla.com/tags/stage/locales

#! /usr/bin/env bash
# Reference https://github.com/mozilla/r2d2b2g/issues/124#issuecomment-17420895

# Current OS is the first parameter. If no parameters are supplied exit
if [ $# -eq 0 ]
  then
    echo "ERROR: no arguments supplied."
    echo "Usage: r2d2b2g_build.sh *system*"
    echo "Where *system* value is the current OS. Accepted values: win, osx, linux32 or linux64."
    echo "Example: r2d2b2g_build.sh linux64"
    exit 1
fi

# Ensure that the OS is one of (win, osx, linux32, linux64). If not exit
case $1 in
  "win")
    currentOS="win";;
  "osx")
    currentOS="osx";;
  "linux32" | "linux64")
    currentOS="linux";;
  *)
    echo "The specified *system* is not valid."
    echo "Accepted values: win, osx, linux32 or linux64."
    echo "Example: r2d2b2g_build.sh linux64"
    exit 1;;
esac

# Store the folder where this script is for later
scriptfolder=${PWD}

if [ ! -d "$scriptfolder/r2d2b2g" ]
  then
    # If the "r2d2b2g" folder does not exists I run the first setup
    # Using --recursive instead of git submodule init; git submodule update
    git clone --recursive git://github.com/mozilla/r2d2b2g.git
    cd r2d2b2g
  else
    # Folder exists: I need to pull everything after stashing pending changes
    # in ./gaia. I don't need any change available there, and sometimes the
    # update get stuck
    cd r2d2b2g/gaia
    git stash
    cd ..
    git pull --recurse-submodules && git submodule update
fi

# Now I can start building
export LOCALES_FILE=${PWD}/gaia/locales/languages_all.json
make locales
make build

# On Linux I have to build a second time with the second platform (linux64 ->
# linux or viceversa)
if [ $1 == "linux32" ]
  then
    B2G_PLATFORM=linux64 make build
fi
if [ $1 == "linux64" ]
  then
    B2G_PLATFORM=linux make build
fi

# Create custom package.json with modified settings
cd $scriptfolder/r2d2b2g/addon

# Copy original package.json to packageoriginal.json. Current folder is
# r2d2b2g/addon
cp package.json packageoriginal.json

# Call update_packagejson.py script to update the content of package.json.
python $scriptfolder/r2d2b2g_jsonupdate.py

# Build the actual package
cd ..
make package

# Restore original package.json
mv $scriptfolder/r2d2b2g/addon/packageoriginal.json $scriptfolder/r2d2b2g/addon/package.json

# Move files in /files and rename it adding -platformname
if [ ! -d "$scriptfolder/files" ]
  then
    # If it doesn't exist I create a "files" folder
    mkdir $scriptfolder/files
fi
mv $scriptfolder/r2d2b2g/addon/r2d2b2g.xpi $scriptfolder/files/r2d2b2g-$currentOS.xpi

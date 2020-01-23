#!/bin/fish

# Script to update the copyright year in header files

set NEW_YEAR (date +"%Y")
set OLD_YEAR (math $NEW_YEAR - 1)
sed -i "s/Copyright  2016-$OLD_YEAR M/Copyright  2016-$NEW_YEAR M/g" silkaj/*.py tests/*.py

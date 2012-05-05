#!/bin/bash
#     This file is part of TexFlasher.
#     Copyright (c) 2012:
#          Can Oezmen
#          Axel Pfeiffer
#
#     TexFlasher is free software: you can redistribute it and/or modify
#     it under the terms of the GNU General Public License as published by
#     the Free Software Foundation, either version 3 of the License, or
#     (at your option) any later version.
# 
#     TexFlasher is distributed in the hope that it will be useful,
#     but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#     GNU General Public License for more details.
# 
#     You should have received a copy of the GNU General Public License
#     along with TexFlasher  If not, see <http://www.gnu.org/licenses/>.


#save files on server

files=$*

# check if svn is available in subfolder
svn info $file > /dev/null
HAVESVN=$?

for thing in $files; do
  svn add $thing 2> /dev/null  
	svn info $thing > /dev/null
	HAVESVN=$?
	if [ $HAVESVN -eq 0 ]; then
# 		echo "svn available for this file"
		svn up $thing 
		svn commit $thing -m "save learning progress"
	fi
# 	else
# 		echo "svn unavailable"
done

exit 0
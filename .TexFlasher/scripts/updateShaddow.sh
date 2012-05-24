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


file=$1
filebase=$(basename $file)
workingDir=$PWD

svn info $file &> /dev/null
HAVESVN=$?
if [ ! $HAVESVN -eq 0 ]; then
	# no svn -> no update!
	exit 0
fi
# only svn revisioned files past this point

lastFolder="`python .TexFlasher/scripts/repoName.py $file`"
shaddowFolder="$workingDir/.$lastFolder"
echo $file
echo $lastFolder

if [ ! -f "$shaddowFolder/$filebase" ]; then
	repoURL="`svn info $workingDir/$lastFolder | grep URL | cut -d ' ' -f2`"
	echo "$repoURL needs to be checked out"
	svn co $repoURL $shaddowFolder
else
	echo "shaddow repository exists."
	svn up $shaddowFolder
fi


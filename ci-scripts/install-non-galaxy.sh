#!/bin/bash

_TOP=$(dirname `readlink -f -- $0`)/..


if [ ! -d ~/.ansible/plugins/modules ]; then
   mkdir -p ~/.ansible/plugins/modules
fi
cd ~/.ansible/plugins/modules

cat $_TOP/non-galaxy.txt | xargs -i git clone {}


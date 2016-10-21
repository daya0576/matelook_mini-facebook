#!/bin/sh

argu_num=$#
if test $argu_num -eq 0; then
    echo "Usage: $0 <commit msg> ..."
    exit
fi


git add .;
git commit -m "$1  ---- auto sync";
git push gitlab master

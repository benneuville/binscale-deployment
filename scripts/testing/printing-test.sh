#!/bin/bash

read -p "Do you wish to install this program? [Y/n]" yn
case $yn in
    [Yy]* ) echo "yessss"; break;;
    [Nn]* ) exit;;
    * ) echo "Please answer yes or no.";;
esac

# JOB="coucou"
# trap "ssh grenoble.g5k \"oardel $JOB\"; printf \"\033[38;5;88mJob $JOB killed.\033[0m\n\"; exit 0" SIGINT


DEFAULT_INPUT_GRAPH_FOLDER="./experience/generator/graphs/"
for file in $DEFAULT_INPUT_GRAPH_FOLDER/*.bs.yaml;
do
    echo "file = $file"
    echo "$(basename "$file" .bs.yaml | tr " " "_")"
done

BRANCH_NAME=17-dep-improve-grid5000-deployment-from-local-machine
# Vérifie s'il y a des changements locaux non commités
if ! git diff --quiet; then
    echo "Erreur : Il y a des changements locaux non commités sur la branche '$BRANCH_NAME'."
    exit 1
fi

# Vérifie s'il y a des commits locaux non poussés vers origin
git fetch origin
if [ "$(git rev-list --count "$BRANCH_NAME"..origin/"$BRANCH_NAME")" -gt 0 ]; then
    echo "Erreur : La branche '$BRANCH_NAME' a des commits locaux non poussés vers origin."
    exit 1
fi

if [ "$(git rev-list --count origin/"$BRANCH_NAME".."$BRANCH_NAME")" -gt 0 ]; then
    echo "Erreur : La branche '$BRANCH_NAME' a des commits locaux non synchronisés avec origin."
    exit 1
fi
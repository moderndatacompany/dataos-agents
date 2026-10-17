#!/bin/sh
case "$1" in
 *sername*) cat /run/showcase-git/username ;;
 *assword*) cat /run/showcase-git/bitbucket-token ;;
 *) exit 1 ;;
esac

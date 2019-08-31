#!/bin/sh

set -e

sh -c "dockerd -H unix:///var/run/docker.sock -H tcp://127.0.0.1:2375 &"
pgrep docker > /dev/null
STATUS=`echo $?`

while [ $STATUS -ne "0" ];
do
  sleep 1
  pgrep docker > /dev/null
  STATUS=`echo $?`
done

python3 -m ecranner
pkill -15 dockerd

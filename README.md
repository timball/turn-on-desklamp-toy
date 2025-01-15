# turn-on-desklight-toy

This is a _toy_, it's probably bad. It turns on a desk light when a video
camera is turned on. Implemented as a shell script that uses `log(1)` on OSX
to watch for video camera "on" events and uses `curl(1)` to toggle the state of
a desk light controlled by [Home Assistant](https://www.home-assistant.io/). 

## Requirements
This script uses OSX `log(1)` tool to detect the state of the camera video device
an then `curl(1)`Home Assistant API to turn on a light.

Configure it by editing `sekrits.sh` and then executing
the `./turn-on-desklight-toy.sh` command out of this directory

## Thanks and Credit
- https://github.com/akburg/elgatokeylight 
- https://vninja.net/2020/12/04/automating-elgato-key-lights-from-touch-bar/
- https://www.kandji.io/blog/mac-logging-and-the-log-command-a-guide-for-apple-admins
- https://developer.apple.com/documentation/os/viewing-log-messages

--timball

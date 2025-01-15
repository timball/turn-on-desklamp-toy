#!/bin/bash -e -o pipefail -u
# -e errexit    exit after first failed command
# -o pipefail   pipe returns exit status of last command that failed
# -u nounset    not allowed to use unset variables
#
# On OSX toggles a Home Assistant smart light if camera
# video stream is turned toggled on or off
#
# --timball@gmail.com
#
# sekrits.sh has the following variables
# HASS_BASE_URL = [URL OF HASS aka http://host:8123]
# BEARER_TOKEN = [from Home Assistant profile LONG_LIVE_TOKEN]
# HASS_DEVICE = [device to toggle aka switch.gosund_wp3_relay or light.kitchen] it is important that HASS_DEVICE in form of device.item
#
# don't let bad things happen to sekrits.sh
#
# Tue Jan 14 20:32:06 EST 2025

source sekrits.sh

DEVICE=$(echo ${HASS_DEVICE} | cut -d'.' -f1)

curl_hass () {
    #echo "${1}"

    curl --location "${HASS_BASE_URL}/api/services/${DEVICE}/${1}" \
        --header 'Content-Type: application/json' \
        --header "Authorization: Bearer ${BEARER_TOKEN}" \
        -o /dev/null \
        -s \
        --data '{"entity_id": "'${HASS_DEVICE}'"}'

}

log stream --predicate 'subsystem == "com.apple.UVCExtension" and composedMessage contains "Post PowerLog"' | while read line; do

    if echo "$line" | grep -E '"VDCAssistant_Power_State" = On;' > /dev/null; then
        curl_hass "turn_on"
    fi
    if echo "$line" | grep -E '"VDCAssistant_Power_State" = Off;' > /dev/null; then
        curl_hass "turn_off"
    fi
done

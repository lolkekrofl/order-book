#!/bin/bash
sleep 5
mkdir -p "$1/TMessagesProj/build/outputs/apk/afat/release"
echo "app id: $2, name: $3, icon: $4" > "$1/TMessagesProj/build/outputs/apk/afat/release/app.apk"
touch "$1/done"

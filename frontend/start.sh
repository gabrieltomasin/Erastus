#!/bin/sh
# Start Next.js in background, then nginx in foreground
node node_modules/.bin/next start &
nginx -g 'daemon off;'

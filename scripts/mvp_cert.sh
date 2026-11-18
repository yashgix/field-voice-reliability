#!/bin/sh
# Local HTTPS for the iPhone test. Makes a certificate authority limited (name constraints) to this Mac's name and
# current Wi-Fi address, and a server certificate signed by it. Files stay in the data folder, outside git.
# Usage: scripts/mvp_cert.sh   (run again if the Mac's Wi-Fi address changes)
set -eu
OUT="$HOME/field-voice-data/mvp/tls"
HOST="$(scutil --get LocalHostName).local"
IP="$(ipconfig getifaddr en0 || true)"
[ -n "$IP" ] || { echo "No Wi-Fi address on en0; connect to Wi-Fi first." >&2; exit 1; }
mkdir -p "$OUT" && cd "$OUT" && umask 077
# The authority is limited to one address, so a new Wi-Fi address needs a new authority (and a new phone profile).
if [ ! -f ca.key ] || [ "$(cat ca.ip 2>/dev/null)" != "$IP" ]; then
  echo "$IP" > ca.ip
  openssl req -x509 -newkey rsa:2048 -nodes -keyout ca.key -out ca.crt -days 90 -sha256 \
    -subj "/CN=Field readings local test CA" \
    -addext "basicConstraints=critical,CA:TRUE,pathlen:0" -addext "keyUsage=critical,keyCertSign,cRLSign" \
    -addext "nameConstraints=critical,permitted;DNS:$HOST,permitted;DNS:localhost,permitted;IP:$IP/255.255.255.255,permitted;IP:127.0.0.1/255.255.255.255"
fi
openssl req -newkey rsa:2048 -nodes -keyout server.key -out server.csr -subj "/CN=$HOST" 2>/dev/null
printf "subjectAltName=DNS:%s,DNS:localhost,IP:%s,IP:127.0.0.1\nextendedKeyUsage=serverAuth\nbasicConstraints=CA:FALSE\n" \
  "$HOST" "$IP" > server.ext
openssl x509 -req -in server.csr -CA ca.crt -CAkey ca.key -CAcreateserial -out server.crt -days 30 -sha256 \
  -extfile server.ext 2>/dev/null
rm -f server.csr server.ext
chmod 600 ca.key server.key
echo "Server certificate for https://$HOST:8443 and https://$IP:8443 (valid 30 days)."
echo "For the iPhone, AirDrop $OUT/ca.crt (see docs/MVP.md)."

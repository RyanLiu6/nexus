#!/bin/sh
set -e

# Background monitor: Wait for tailscale0 and tun0, then ensure iptables rules are active
(
  while true; do
    if ip link show tailscale0 >/dev/null 2>&1 && ip link show tun0 >/dev/null 2>&1; then
      iptables -C FORWARD -i tailscale0 -o tun0 -j ACCEPT >/dev/null 2>&1 || \
        iptables -A FORWARD -i tailscale0 -o tun0 -j ACCEPT

      iptables -C FORWARD -i tun0 -o tailscale0 -m conntrack --ctstate RELATED,ESTABLISHED -j ACCEPT >/dev/null 2>&1 || \
        iptables -A FORWARD -i tun0 -o tailscale0 -m conntrack --ctstate RELATED,ESTABLISHED -j ACCEPT

      iptables -t nat -C POSTROUTING -o tun0 -j MASQUERADE >/dev/null 2>&1 || \
        iptables -t nat -A POSTROUTING -o tun0 -j MASQUERADE

      # Wait 10s before checking again so rules remain active even if gluetun restarts its tunnel
      sleep 10
    else
      sleep 2
    fi
  done
) &

exec /usr/local/bin/containerboot "$@"

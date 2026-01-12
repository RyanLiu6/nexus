# Root domain A record
resource "cloudflare_record" "root" {
  zone_id = var.cloudflare_zone_id
  name    = "@"
  value   = var.public_ip
  type    = "A"
  ttl     = 1
  proxied = var.proxied
}

# Wildcard subdomain A record
resource "cloudflare_record" "wildcard" {
  zone_id = var.cloudflare_zone_id
  name    = "*"
  value   = var.public_ip
  type    = "A"
  ttl     = 1
  proxied = var.proxied
}

# Subdomain records (foundry, plex, etc.)
resource "cloudflare_record" "subdomains" {
  for_each = var.subdomains
  zone_id  = var.cloudflare_zone_id
  name     = each.key
  value    = var.public_ip
  type     = "A"
  ttl      = 1
  proxied  = var.proxied
}

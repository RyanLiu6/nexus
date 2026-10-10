data "http" "myip" {
  url = "https://ifconfig.me/ip"
}

variable "public_subdomains" {
  description = "List of subdomains to expose publicly via Cloudflare Proxy"
  type        = set(string)
  default     = []
}

resource "cloudflare_dns_record" "public_subdomains" {
  for_each = var.public_subdomains
  zone_id  = var.cloudflare_zone_id
  name     = each.key
  content  = trimspace(data.http.myip.response_body)
  type     = "A"
  ttl      = 1
  proxied  = true
}

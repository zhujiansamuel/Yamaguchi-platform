# SSL Certificates

Place your SSL certificates in this directory:

- `cert.pem` - SSL certificate (with full chain)
- `key.pem` - Private key file

## Generate Self-Signed Certificate (Development Only)

```bash
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout key.pem \
  -out cert.pem \
  -subj "/C=JP/ST=Yamaguchi/L=Yamaguchi/O=Development/CN=data.yamaguchi.lan"
```

## Production

Use certificates from your CA or Let's Encrypt.

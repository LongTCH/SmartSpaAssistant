# SSL Certificate Setup

## Required Files

Place your SSL certificate files in the `nginx/ssl/certs/` directory with the following names:

1. `certificate.crt` - Your SSL certificate (combined with CA bundle)
2. `private.key` - Your private key

## Certificate Chain Setup

If you have separate certificate and CA bundle files, you need to combine them:

1. Copy your `certificate.crt` file to `nginx/ssl/certs/certificate.crt`
2. Append the CA bundle to create a complete certificate chain:

```bash
cat certificate.crt ca_bundle.crt > nginx/ssl/certs/certificate.crt
```

3. Copy your `private.key` file to `nginx/ssl/certs/private.key`

## File Structure

```
nginx/
├── ssl/
│   ├── certs/
│   │   ├── certificate.crt (certificate + CA bundle)
│   │   └── private.key
│   └── README.md
└── nginx.conf
```

## Testing SSL Configuration

After placing the certificate files:

1. Restart the nginx container:

   ```bash
   docker-compose restart nginx
   ```

2. Test the SSL configuration:

   ```bash
   # Test HTTPS connection
   curl -k https://localhost

   # Test HTTP to HTTPS redirect
   curl -I http://localhost
   ```

## Security Notes

- Ensure certificate files have appropriate permissions (600 for private key)
- The private key should never be shared or committed to version control
- Consider using environment variables for certificate paths in production

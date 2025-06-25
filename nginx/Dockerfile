# Use the official nginx alpine image
FROM nginx:alpine

# Copy the nginx configuration file
COPY nginx.dev.conf /etc/nginx/nginx.conf

# Expose port 80
EXPOSE 80

# Start nginx in foreground mode
CMD ["nginx", "-g", "daemon off;"]

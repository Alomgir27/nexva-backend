#!/bin/bash

# Add Nexva backend proxy to existing port 8000 server
# This will add /api route WITHOUT affecting your existing server

echo "🔍 Checking existing port 8000 server..."

PID_8000=$(ss -tulpn 2>/dev/null | grep ":8000 " | grep -oP 'pid=\K[0-9]+' | head -1)

if [ -z "$PID_8000" ]; then
    echo "❌ No server found on port 8000"
    echo "   Your existing server might be down"
    exit 1
fi

CMD_8000=$(ps -p $PID_8000 -o cmd= 2>/dev/null)
echo "   Found: $CMD_8000 (PID: $PID_8000)"

# Check if it's nginx
if echo "$CMD_8000" | grep -q "nginx"; then
    echo "   ✅ Detected nginx - will add location block"
    
    # Backup existing config
    cp -n /etc/nginx/sites-enabled/default /etc/nginx/sites-enabled/default.backup 2>/dev/null || true
    
    # Add nexva-api location block to existing config
    NGINX_CONF=$(find /etc/nginx/sites-enabled -type f | head -1)
    
    if grep -q "location /api" "$NGINX_CONF" 2>/dev/null; then
        echo "   ⚠️  /api location already exists in nginx config"
    else
        # Find the last closing brace and insert before it
        sed -i '/^}$/i \
    # Nexva Backend API\
    location /api {\
        rewrite ^/api/(.*) /$1 break;\
        proxy_pass http://127.0.0.1:8080;\
        proxy_http_version 1.1;\
        proxy_set_header Upgrade $http_upgrade;\
        proxy_set_header Connection "upgrade";\
        proxy_set_header Host $host;\
        proxy_set_header X-Real-IP $remote_addr;\
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;\
    }\
' "$NGINX_CONF"
        
        nginx -t && (systemctl reload nginx 2>/dev/null || service nginx reload)
        echo "   ✅ Added /api route to nginx"
    fi
else
    echo "   ℹ️  Port 8000 is not nginx - using socat tunnel instead"
    
    apt-get install -y socat >/dev/null 2>&1
    
    # Kill any existing socat on 9000
    pkill -f "socat.*9000.*8080" 2>/dev/null || true
    
    # Create tunnel from 9000 -> 8080
    nohup socat TCP-LISTEN:9000,fork TCP:127.0.0.1:8080 > /dev/null 2>&1 &
    
    echo "   ✅ Created port tunnel 9000 -> 8080"
    echo ""
    echo "   Ask RunPod to expose port 9000, or contact support"
fi

echo ""
echo "🌐 Your APIs:"
echo "   Existing:  https://yueihds3xl383a-8000.proxy.runpod.net/"
echo "   Nexva API: https://yueihds3xl383a-8000.proxy.runpod.net/api/docs"
echo ""



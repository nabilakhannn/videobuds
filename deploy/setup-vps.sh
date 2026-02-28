#!/bin/bash
# ================================================================
# VideoBuds VPS Setup Script — Hostinger Ubuntu
# ================================================================
# Run this on your VPS as root:
#   bash setup-vps.sh yourdomain.com
#
# It will install everything and get your app running.
# ================================================================

DOMAIN="$1"

if [ -z "$DOMAIN" ]; then
    echo ""
    echo "❌  Please provide your domain name."
    echo "    Usage: bash setup-vps.sh yourdomain.com"
    echo ""
    exit 1
fi

echo ""
echo "🚀 Setting up VideoBuds on $DOMAIN"
echo "================================================"
echo ""

# ── 1. Update system ─────────────────────────────────────────────
echo "📦 Step 1/8: Updating system packages..."
apt-get update -qq && apt-get upgrade -y -qq

# ── 2. Install Nginx, PostgreSQL, Certbot, Git ──────────────────
echo "📦 Step 2/8: Installing Nginx, PostgreSQL, Certbot..."
apt-get install -y -qq \
    nginx postgresql postgresql-contrib \
    certbot python3-certbot-nginx \
    git ufw

# ── Install Python with venv support ────────────────────────────
echo "🐍 Step 2b/8: Setting up Python..."

# Try python3.11 first, then PPA, then fall back to system python3
if command -v python3.11 &>/dev/null; then
    PYTHON=python3.11
    echo "   Found python3.11"
elif apt-get install -y -qq python3.11 python3.11-venv python3.11-dev 2>/dev/null; then
    PYTHON=python3.11
    echo "   Installed python3.11"
else
    echo "   python3.11 not available, trying deadsnakes PPA..."
    apt-get install -y -qq software-properties-common 2>/dev/null
    if add-apt-repository -y ppa:deadsnakes/ppa 2>/dev/null && apt-get update -qq 2>/dev/null && apt-get install -y -qq python3.11 python3.11-venv python3.11-dev 2>/dev/null; then
        PYTHON=python3.11
        echo "   Installed python3.11 from PPA"
    else
        # Fall back to system python3
        PYTHON=python3
        apt-get install -y -qq python3-venv python3-dev python3-pip
        echo "   Using system $($PYTHON --version)"
    fi
fi

# Verify Python works
if ! $PYTHON --version &>/dev/null; then
    echo "❌ Python not found. Cannot continue."
    exit 1
fi
echo "   ✅ Using $($PYTHON --version)"

# ── 3. Set up PostgreSQL database ────────────────────────────────
echo "🗄️  Step 3/8: Setting up PostgreSQL database..."

# Make sure PostgreSQL is running
systemctl start postgresql
systemctl enable postgresql

DB_PASS=$(openssl rand -hex 16)

sudo -u postgres psql -tc "SELECT 1 FROM pg_roles WHERE rolname='videobuds'" | grep -q 1 || \
    sudo -u postgres psql -c "CREATE USER videobuds WITH PASSWORD '$DB_PASS';"

sudo -u postgres psql -tc "SELECT 1 FROM pg_database WHERE datname='videobuds'" | grep -q 1 || \
    sudo -u postgres psql -c "CREATE DATABASE videobuds OWNER videobuds;"

echo "   ✅ Database ready"

# ── 4. Create app user and clone code ────────────────────────────
echo "📂 Step 4/8: Setting up app directory..."

# Create app user if not exists
id -u videobuds &>/dev/null || useradd -m -s /bin/bash videobuds

APP_DIR="/home/videobuds/app"

if [ -d "$APP_DIR" ]; then
    echo "   App directory exists, pulling latest code..."
    cd "$APP_DIR" && sudo -u videobuds git pull origin main
else
    sudo -u videobuds git clone https://github.com/nabilakhannn/videobuds.git "$APP_DIR"
fi

cd "$APP_DIR"
echo "   ✅ Code ready"

# ── 5. Python virtual environment + dependencies ────────────────
echo "🐍 Step 5/8: Installing Python dependencies..."
sudo -u videobuds $PYTHON -m venv "$APP_DIR/venv"
sudo -u videobuds "$APP_DIR/venv/bin/pip" install --quiet --upgrade pip
sudo -u videobuds "$APP_DIR/venv/bin/pip" install --quiet -r "$APP_DIR/requirements.txt"
sudo -u videobuds "$APP_DIR/venv/bin/pip" install --quiet -r "$APP_DIR/tools/requirements.txt" 2>/dev/null || true
echo "   ✅ Dependencies installed"

# ── 6. Create .env file ─────────────────────────────────────────
echo "🔐 Step 6/8: Creating environment file..."
SECRET=$(openssl rand -hex 32)

ENV_FILE="$APP_DIR/.env"

# Only create .env if it doesn't already exist (don't overwrite API keys)
if [ ! -f "$ENV_FILE" ]; then
    cat > "$ENV_FILE" << ENVEOF
SECRET_KEY=$SECRET
FLASK_ENV=production
DATABASE_URL=postgresql://videobuds:$DB_PASS@localhost:5432/videobuds

# Add your API keys below:
GOOGLE_API_KEY=
WAVESPEED_API_KEY=
# KIE_API_KEY=
# HIGGSFIELD_API_KEY_ID=
# HIGGSFIELD_API_KEY_SECRET=
ENVEOF
    chown videobuds:videobuds "$ENV_FILE"
    chmod 600 "$ENV_FILE"
    echo "   ✅ Environment file created"
    echo "   ⚠️  You still need to add your GOOGLE_API_KEY and WAVESPEED_API_KEY!"
else
    echo "   ✅ Environment file already exists (not overwritten)"
fi

# Create upload directories
mkdir -p "$APP_DIR/app/static/uploads" "$APP_DIR/app/static/generated"
chown -R videobuds:videobuds "$APP_DIR/app/static/uploads" "$APP_DIR/app/static/generated"

# ── 7. Create systemd service (keeps app running forever) ───────
echo "⚙️  Step 7/8: Setting up app service..."

cat > /etc/systemd/system/videobuds.service << SVCEOF
[Unit]
Description=VideoBuds Web Application
After=network.target postgresql.service

[Service]
User=videobuds
Group=videobuds
WorkingDirectory=$APP_DIR
Environment="PATH=$APP_DIR/venv/bin:/usr/bin"
EnvironmentFile=$APP_DIR/.env
ExecStart=$APP_DIR/venv/bin/gunicorn run:app --bind 127.0.0.1:8080 --workers 2 --threads 4 --timeout 120
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
SVCEOF

systemctl daemon-reload
systemctl enable videobuds
systemctl restart videobuds
echo "   ✅ App service started"

# ── 8. Configure Nginx (web server + your domain) ───────────────
echo "🌐 Step 8/8: Setting up Nginx for $DOMAIN..."

cat > /etc/nginx/sites-available/videobuds << NGXEOF
server {
    listen 80;
    server_name $DOMAIN www.$DOMAIN;

    client_max_body_size 16M;

    location / {
        proxy_pass http://127.0.0.1:8080;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_read_timeout 300s;
    }

    location /static/ {
        alias $APP_DIR/app/static/;
        expires 7d;
    }
}
NGXEOF

# Enable site
ln -sf /etc/nginx/sites-available/videobuds /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default

nginx -t && systemctl restart nginx

# ── Firewall ─────────────────────────────────────────────────────
ufw allow 'Nginx Full' >/dev/null 2>&1
ufw allow OpenSSH >/dev/null 2>&1
echo "y" | ufw enable >/dev/null 2>&1

# ── SSL Certificate (HTTPS) ─────────────────────────────────────
echo ""
echo "🔒 Setting up HTTPS (free SSL certificate)..."
certbot --nginx -d "$DOMAIN" -d "www.$DOMAIN" --non-interactive --agree-tos --register-unsafely-without-email || {
    echo "   ⚠️  SSL setup failed — your domain DNS may not be pointing to this server yet."
    echo "   Run this later after DNS is set: certbot --nginx -d $DOMAIN -d www.$DOMAIN"
}

echo ""
echo "================================================"
echo "✅ VideoBuds is LIVE!"
echo "================================================"
echo ""
echo "🌐 Visit: https://$DOMAIN"
echo "🔑 Login: admin@videobuds.com / admin"
echo ""
echo "⚠️  IMPORTANT — You still need to:"
echo "   Add your API keys: nano $ENV_FILE"
echo "   Then restart:      systemctl restart videobuds"
echo ""
echo "📋 Useful commands:"
echo "   Check status:    systemctl status videobuds"
echo "   View logs:       journalctl -u videobuds -f"
echo "   Restart app:     systemctl restart videobuds"
echo "   Edit settings:   nano $ENV_FILE"
echo "   Update code:     cd $APP_DIR && git pull && systemctl restart videobuds"
echo ""

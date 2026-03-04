#!/bin/bash

# SCI-Manager Production Deployment Script for Scaleway VPS
# Usage: ./deploy.sh

set -e

echo "🚀 Starting SCI-Manager deployment on Scaleway VPS"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
DOMAIN=${DOMAIN:-"your-domain.com"}
EMAIL=${EMAIL:-"admin@your-domain.com"}

echo -e "${YELLOW}Domain: $DOMAIN${NC}"
echo -e "${YELLOW}Email: $EMAIL${NC}"

# Update system
echo -e "${GREEN}📦 Updating system packages...${NC}"
sudo apt update && sudo apt upgrade -y

# Install required packages
echo -e "${GREEN}📦 Installing Docker and dependencies...${NC}"
sudo apt install -y apt-transport-https ca-certificates curl gnupg lsb-release ufw

# Install Docker
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

# Start and enable Docker
sudo systemctl start docker
sudo systemctl enable docker

# Add current user to docker group
sudo usermod -aG docker $USER

# Configure firewall
echo -e "${GREEN}🔥 Configuring firewall...${NC}"
sudo ufw --force enable
sudo ufw allow ssh
sudo ufw allow 80
sudo ufw allow 443
sudo ufw --force reload

# Create application directory
echo -e "${GREEN}📁 Creating application directory...${NC}"
sudo mkdir -p /opt/sci-manager
sudo chown -R $USER:$USER /opt/sci-manager

# Copy application files
echo -e "${GREEN}📋 Copying application files...${NC}"
cp -r . /opt/sci-manager/
cd /opt/sci-manager

# Create SSL directory
mkdir -p docker/ssl

# Install Certbot for SSL
echo -e "${GREEN}🔒 Installing Certbot for SSL certificates...${NC}"
sudo apt install -y certbot

# Create .env file from production template
if [ ! -f .env ]; then
    echo -e "${YELLOW}⚠️  Creating .env file from template...${NC}"
    cp .env.production .env
    echo -e "${RED}❗ Please edit .env file with your actual values before continuing!${NC}"
    echo -e "${YELLOW}Run: nano .env${NC}"
    exit 1
fi

# Build and start services
echo -e "${GREEN}🐳 Building and starting Docker services...${NC}"
docker compose down || true
docker compose build --no-cache
docker compose up -d

# Wait for services to be ready
echo -e "${GREEN}⏳ Waiting for services to be ready...${NC}"
sleep 30

# Check if services are running
echo -e "${GREEN}🔍 Checking service status...${NC}"
docker compose ps

# Get SSL certificate (temporary - will be automated)
echo -e "${YELLOW}⚠️  SSL Certificate Setup:${NC}"
echo -e "1. Make sure your domain DNS points to this VPS IP: $(curl -s ifconfig.me)"
echo -e "2. Run SSL setup manually after DNS propagation:"
echo -e "   sudo certbot certonly --standalone -d $DOMAIN"
echo -e "3. Copy certificates to docker/ssl/:"
echo -e "   sudo cp /etc/letsencrypt/live/$DOMAIN/fullchain.pem docker/ssl/"
echo -e "   sudo cp /etc/letsencrypt/live/$DOMAIN/privkey.pem docker/ssl/"
echo -e "4. Restart services: docker compose restart nginx"

# Setup automatic SSL renewal
echo -e "${GREEN}🔄 Setting up SSL certificate renewal...${NC}"
sudo crontab -l | { cat; echo "0 12 * * * /usr/bin/certbot renew --quiet && docker compose restart nginx"; } | sudo crontab -

# Create backup script
cat > backup.sh << 'EOF'
#!/bin/bash
# Database backup script
BACKUP_DIR="/opt/sci-manager/backups"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR

# Backup database
docker compose exec -T db pg_dump -U sci_manager sci_manager_prod > $BACKUP_DIR/backup_$DATE.sql

# Keep only last 7 backups
cd $BACKUP_DIR && ls -t backup_*.sql | tail -n +8 | xargs rm -f

echo "Backup completed: $BACKUP_DIR/backup_$DATE.sql"
EOF

chmod +x backup.sh

# Setup backup cron job
sudo crontab -l | { cat; echo "0 2 * * * /opt/sci-manager/backup.sh"; } | sudo crontab -

echo -e "${GREEN}✅ Deployment completed!${NC}"
echo -e "${GREEN}🌐 Your application should be available at: https://$DOMAIN${NC}"
echo -e "${YELLOW}📋 Next steps:${NC}"
echo -e "1. Configure your .env file with production values"
echo -e "2. Setup SSL certificates with Certbot"
echo -e "3. Test the application"
echo -e "4. Configure monitoring and alerts"

# Display service status
echo -e "${GREEN}📊 Service Status:${NC}"
docker compose logs --tail=20
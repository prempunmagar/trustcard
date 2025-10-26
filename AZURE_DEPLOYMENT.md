# TrustCard Deployment on Azure VM

Complete guide for deploying TrustCard to Azure Virtual Machine with Docker.

## Quick Start Summary

1. Create Ubuntu VM on Azure (B2s or B2ms)
2. SSH into VM
3. Install Docker and Docker Compose
4. Clone repo and configure .env
5. Run docker-compose -f docker-compose.prod.yml up -d
6. Access at http://YOUR_VM_IP:8000

## Detailed Steps

### Step 1: Create Azure VM

**Using Azure Portal:**
- Go to portal.azure.com
- Create Resource > Ubuntu Server 22.04 LTS
- Size: B2s (2 vCPU, 4GB RAM) - 0/month OR B2ms (2 vCPU, 8GB RAM) - 0/month (Recommended)
- Open ports: 22 (SSH), 80 (HTTP), 443 (HTTPS)
- Download SSH key (.pem file)

**Or use Azure CLI:**
```bash
az login
az group create --name trustcard-rg --location eastus
az vm create --resource-group trustcard-rg --name trustcard-vm --image Ubuntu2204 --size Standard_B2s --admin-username azureuser --generate-ssh-keys
az vm open-port --port 80 --resource-group trustcard-rg --name trustcard-vm
az vm open-port --port 443 --resource-group trustcard-rg --name trustcard-vm
```

### Step 2: Connect to VM

```bash
ssh -i your-key.pem azureuser@YOUR_VM_PUBLIC_IP
```

### Step 3: Install Docker

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Log out and back in
exit
# SSH back in
```

### Step 4: Clone and Configure

```bash
git clone https://github.com/prempunmagar/trustcard.git
cd trustcard
cp .env.example .env
nano .env  # Edit with your production values
```

**Important .env values:**
- DATABASE_URL password
- SECRET_KEY (generate with: python3 -c "import secrets; print(secrets.token_urlsafe(50))")
- ANTHROPIC_API_KEY
- INSTAGRAM credentials

### Step 5: Deploy

```bash
docker-compose -f docker-compose.prod.yml up -d --build
docker-compose -f docker-compose.prod.yml ps
docker-compose -f docker-compose.prod.yml logs -f
```

### Step 6: Test

```bash
curl http://localhost:8000/health
# From your computer: http://YOUR_VM_IP:8000/health
```

### Step 7: Setup Nginx (Optional)

```bash
sudo apt install nginx -y
sudo nano /etc/nginx/sites-available/trustcard
```

Add config and enable:
```bash
sudo ln -s /etc/nginx/sites-available/trustcard /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

## Management Commands

```bash
# View logs
docker-compose -f docker-compose.prod.yml logs -f api

# Restart
docker-compose -f docker-compose.prod.yml restart

# Update code
git pull && docker-compose -f docker-compose.prod.yml up -d --build

# Backup database
docker exec trustcard-db pg_dump -U trustcard trustcard > backup.sql

# Scale workers
docker-compose -f docker-compose.prod.yml up -d --scale celery_worker=5
```

## Security

```bash
sudo ufw allow OpenSSH
sudo ufw allow 'Nginx Full'
sudo ufw enable
```

## Cost

- B2s VM: ~0/month
- B2ms VM: ~0/month (recommended)
- Storage: ~/month
- Total: ~5-65/month

---

See DEPLOYMENT.md for more detailed instructions.

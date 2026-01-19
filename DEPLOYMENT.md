# Deployment Guide for Aura

This guide covers multiple deployment options for the Aura conversational AI webapp.

## Quick Deployment Options

### Option 1: Railway (Recommended - Easiest)

Railway provides automatic deployments from GitHub and SSL certificates.

1. **Push your code to GitHub**
   ```bash
   git add .
   git commit -m "Ready for deployment"
   git push origin main
   ```

2. **Deploy on Railway:**
   - Go to [railway.app](https://railway.app)
   - Click "New Project" → "Deploy from GitHub repo"
   - Select your repository
   - **Important:** Railway will use Python 3.11 (specified in `runtime.txt` and `nixpacks.toml`)
   - **CRITICAL: Add environment variables in Railway dashboard:**
     - Go to your project → Variables tab (or Settings → Variables)
     - Click "New Variable" and add each of these:
     
     **Required Variables:**
     - Variable: `HUME_API_KEY` → Value: `your_actual_hume_api_key`
     - Variable: `GOOGLE_ADK_API_KEY` → Value: `your_actual_google_api_key`
     
     **Optional Variables (recommended):**
     - Variable: `GOOGLE_ADK_MODEL_NAME` → Value: `gemini-2.5-flash-lite`
     - Variable: `LLM_PROVIDER` → Value: `gemini`
     - Variable: `DEBUG` → Value: `False`
     - Variable: `LOG_LEVEL` → Value: `INFO`
     
     **Note:** Do NOT commit your .env file to GitHub! Railway uses environment variables set in the dashboard.
   
   - Railway will detect Python 3.11 and deploy
   - Your app will be live at `https://your-app.railway.app`

**Note:** The build configuration uses Python 3.11 to avoid compatibility issues with pydantic-core and Python 3.13.

### Option 2: Render

1. **Create a Render account** at [render.com](https://render.com)

2. **Create a new Web Service:**
   - Connect your GitHub repository
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `uvicorn app:app --host 0.0.0.0 --port $PORT`
   - Environment: Python 3

3. **Add Environment Variables:**
   - `HUME_API_KEY`
   - `GOOGLE_ADK_API_KEY`
   - `GOOGLE_ADK_MODEL_NAME=gemini-2.5-flash-lite`
   - `LOG_LEVEL=INFO`

### Option 3: Fly.io

1. **Install Fly CLI:**
   ```bash
   curl -L https://fly.io/install.sh | sh
   ```

2. **Login:**
   ```bash
   fly auth login
   ```

3. **Create fly.toml** (see below)

4. **Deploy:**
   ```bash
   fly deploy
   ```

### Option 4: Heroku

1. **Install Heroku CLI**

2. **Create Procfile:**
   ```
   web: uvicorn app:app --host 0.0.0.0 --port $PORT
   ```

3. **Deploy:**
   ```bash
   heroku create your-app-name
   heroku config:set HUME_API_KEY=your_key
   heroku config:set GOOGLE_ADK_API_KEY=your_key
   git push heroku main
   ```

### Option 5: DigitalOcean App Platform

1. **Connect GitHub repository**
2. **Configure:**
   - Build Command: `pip install -r requirements.txt`
   - Run Command: `uvicorn app:app --host 0.0.0.0 --port $PORT`
3. **Add environment variables**
4. **Deploy**

### Option 6: Self-Hosted (VPS)

#### Using systemd (Linux)

1. **SSH into your server**

2. **Install dependencies:**
   ```bash
   sudo apt update
   sudo apt install python3-pip python3-venv nginx
   ```

3. **Clone repository:**
   ```bash
   git clone <your-repo-url> /var/www/aura
   cd /var/www/aura
   ```

4. **Set up Python environment:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

5. **Create .env file:**
   ```bash
   nano .env
   # Add your API keys
   ```

6. **Create systemd service** (`/etc/systemd/system/aura.service`):
   ```ini
   [Unit]
   Description=Aura Conversational AI
   After=network.target

   [Service]
   User=www-data
   WorkingDirectory=/var/www/aura
   Environment="PATH=/var/www/aura/venv/bin"
   ExecStart=/var/www/aura/venv/bin/uvicorn app:app --host 0.0.0.0 --port 8000
   Restart=always

   [Install]
   WantedBy=multi-user.target
   ```

7. **Start service:**
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable aura
   sudo systemctl start aura
   ```

8. **Configure Nginx** (`/etc/nginx/sites-available/aura`):
   ```nginx
   server {
       listen 80;
       server_name your-domain.com;

       location / {
           proxy_pass http://127.0.0.1:8000;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
           proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
           proxy_set_header X-Forwarded-Proto $scheme;
       }
   }
   ```

9. **Enable site:**
   ```bash
   sudo ln -s /etc/nginx/sites-available/aura /etc/nginx/sites-enabled/
   sudo nginx -t
   sudo systemctl restart nginx
   ```

10. **Set up SSL with Let's Encrypt:**
    ```bash
    sudo apt install certbot python3-certbot-nginx
    sudo certbot --nginx -d your-domain.com
    ```

#### Using Docker (Recommended for VPS)

1. **Create Dockerfile** (see below)

2. **Create docker-compose.yml:**
   ```yaml
   version: '3.8'
   services:
     aura:
       build: .
       ports:
         - "8000:8000"
       env_file:
         - .env
       restart: unless-stopped
   ```

3. **Deploy:**
   ```bash
   docker-compose up -d
   ```

## Production Checklist

- [ ] Set `DEBUG=False` in environment variables
- [ ] Set strong API keys in environment variables
- [ ] Configure CORS to only allow your domain
- [ ] Set up SSL/HTTPS (required for microphone access)
- [ ] Configure logging to file or external service
- [ ] Set up monitoring/health checks
- [ ] Configure backup for conversation data (if using database)
- [ ] Set appropriate port (use environment variable)

## Environment Variables for Production

```env
# Required
HUME_API_KEY=your_key
GOOGLE_ADK_API_KEY=your_key

# Recommended
DEBUG=False
LOG_LEVEL=INFO
GOOGLE_ADK_MODEL_NAME=gemini-2.5-flash-lite

# Optional
LLM_PROVIDER=gemini
LLM_API_URL=https://generativelanguage.googleapis.com/v1beta
HUME_API_URL=https://api.hume.ai
```

## Security Notes

1. **Never commit `.env` file** - it's in `.gitignore`
2. **Use HTTPS** - Required for microphone access
3. **Restrict CORS** - Update `app.py` to only allow your domain:
   ```python
   allow_origins=["https://yourdomain.com"]
   ```
4. **Rate limiting** - Consider adding rate limiting for production
5. **API key rotation** - Regularly rotate your API keys

## Monitoring

- Health check endpoint: `GET /api/health`
- Check logs: Most platforms provide log viewing in dashboard
- Monitor API usage: Check quotas in Google Cloud Console and Hume.ai dashboard

## Troubleshooting

### Port Issues
- Ensure port 8000 (or configured port) is open in firewall
- Check if port is already in use: `lsof -i :8000`

### Environment Variables
- Verify all required variables are set
- Check logs for "NOT_SET" warnings
- Ensure `.env` file is in project root

### SSL/HTTPS
- Microphone access requires HTTPS
- Use Let's Encrypt for free SSL certificates
- Ensure certificates are auto-renewing

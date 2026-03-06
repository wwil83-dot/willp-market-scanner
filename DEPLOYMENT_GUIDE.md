# WillP ProLine Scanner - Cloud Deployment Guide

## 🚀 Deploy to Render (FREE)

### Step 1: Create GitHub Repository

1. Go to https://github.com and sign in (or create free account)
2. Click "New repository" (green button)
3. Name it: `willp-market-scanner`
4. Make it **Public** (required for free tier)
5. Click "Create repository"

### Step 2: Upload Your Files

On the repository page, click "uploading an existing file":

**Upload these 4 files:**
- `scanner_backend_acl.py`
- `market_scanner_improved.html`
- `requirements.txt`
- `Procfile`
- `runtime.txt`

Then click "Commit changes"

### Step 3: Deploy to Render

1. Go to https://render.com
2. Sign up for FREE account (use GitHub to sign in - easiest)
3. Click "New +" → "Web Service"
4. Click "Connect account" to connect GitHub
5. Find your `willp-market-scanner` repository
6. Click "Connect"

**Configure the service:**
- **Name:** `willp-scanner` (or anything you like)
- **Environment:** `Python 3`
- **Build Command:** `pip install -r requirements.txt`
- **Start Command:** `gunicorn scanner_backend_acl:app --timeout 120 --workers 2`
- **Plan:** Select **FREE** tier

7. Click "Create Web Service"

### Step 4: Wait for Deployment

- First deployment takes 5-10 minutes
- You'll see build logs scrolling
- When done, you'll see "Live" with a green checkmark
- Your URL will be: `https://willp-scanner.onrender.com` (or similar)

### Step 5: Access Your Scanner

Open the URL in any browser, on any device, anywhere!

**Note:** Free tier spins down after 15 minutes of inactivity. First load after inactivity takes ~60 seconds (cold start + ACL calculation).

---

## 🌐 Alternative: PythonAnywhere (Simpler but slower)

### Step 1: Create Account
1. Go to https://www.pythonanywhere.com
2. Create FREE "Beginner" account

### Step 2: Upload Files
1. Go to "Files" tab
2. Upload all 5 files to `/home/yourusername/`

### Step 3: Install Dependencies
1. Go to "Consoles" tab
2. Start a "Bash" console
3. Run:
```bash
pip3 install --user flask flask-cors yfinance pandas numpy
```

### Step 4: Setup Web App
1. Go to "Web" tab
2. Click "Add a new web app"
3. Choose "Flask"
4. Python version: 3.10
5. Path: `/home/yourusername/scanner_backend_acl.py`
6. Click through to finish

### Step 5: Configure
1. In "Web" tab, find "WSGI configuration file"
2. Click to edit
3. Change the path to your app
4. Save and click "Reload"

Your scanner will be live at: `https://yourusername.pythonanywhere.com`

---

## 📱 Access From Anywhere

Once deployed, you can access your scanner from:
- ✅ Any web browser
- ✅ Phone (add to home screen for app-like experience)
- ✅ Tablet
- ✅ Work computer
- ✅ Anywhere with internet!

---

## 🔧 Updating Your Scanner

**If you make changes:**

1. Update files in GitHub repository
2. Render automatically redeploys (takes ~2 minutes)
3. Or manually trigger "Deploy latest commit" in Render dashboard

---

## 💡 Tips

- **Bookmark the URL** for quick access
- **Add to phone home screen** for app-like experience
- **Free tier limitations:** 
  - Render: 750 hours/month (plenty for personal use)
  - Spins down after 15 min inactivity (cold start on first load)
- **To keep always-on:** Paid tier is $7/month (optional)

---

## 🆘 Troubleshooting

**Build fails on Render?**
- Check that all 5 files are in GitHub
- Make sure repository is Public

**Scanner loads but shows error?**
- Check Render logs (click "Logs" tab)
- yfinance might be blocked - try PythonAnywhere instead

**Slow to load?**
- First load after inactivity takes 60 seconds (normal)
- Subsequent loads are fast (cached for 3 min)

---

Need help? The deployment process is straightforward - should take ~15 minutes total! 🚀

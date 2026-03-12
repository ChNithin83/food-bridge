# Deployment Guide - Render

## Prerequisites
1. GitHub account (to push your code)
2. Render account (https://render.com)
3. Your code pushed to a GitHub repository

## Step 1: Prepare Your Code for Deployment

✅ **Already Done:**
- Created `Procfile` - tells Render how to run your app
- Created `render.yaml` - optional deployment config
- Updated `app.py` to use environment PORT variable
- `requirements.txt` includes production dependencies

## Step 2: Push to GitHub

```bash
# Initialize git (if not already done)
git init

# Add all files
git add .

# Commit
git commit -m "Prepare for Render deployment"

# Add remote (replace YOUR_USERNAME and REPO_NAME)
git remote add origin https://github.com/YOUR_USERNAME/REPO_NAME.git
git branch -M main
git push -u origin main
```

## Step 3: Create Render Service

1. Go to https://render.com
2. Sign up / Sign in
3. Click **New →** **Web Service**
4. Connect your GitHub repository
5. Select your `food-bridge` repo
6. Fill in details:
   - **Name:** food-bridge (or your preferred name)
   - **Runtime:** Python 3.9
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `gunicorn app:app`
   - **Branch:** main
   - **Plan:** Free (or paid, your choice)

## Step 4: Set Environment Variables

In the Render dashboard for your service:
1. Go to **Environment** tab
2. Add these variables:
   ```
   FLASK_ENV = production
   SECRET_KEY = your_secure_random_key_here
   EMAIL_ADDRESS = your_email@gmail.com
   EMAIL_PASSWORD = your_app_password
   DATABASE_URL = (if using PostgreSQL instead of SQLite)
   ```

## Step 5: Deploy

1. Click **Create Web Service**
2. Render will automatically start building and deploying
3. Once live, you'll get a URL like: `https://food-bridge-xxxxx.onrender.com`

## Recommended Updates for Production

### 1. Update app.py to use environment variables (security):
```python
# Replace hardcoded values with:
EMAIL_ADDRESS = os.environ.get('EMAIL_ADDRESS', 'your_gmail@gmail.com')
EMAIL_PASSWORD = os.environ.get('EMAIL_PASSWORD', 'your_app_password_here')
app.secret_key = os.environ.get('SECRET_KEY', 'food_waste_secret_key_2024')
```

### 2. For database persistence (optional):
- Free SQLite works but resets on deploys
- Upgrade to PostgreSQL in Render for persistent data

### 3. Auto-redeploy on push:
- Render automatically redeploys when you push to GitHub

## Troubleshooting

- **"ModuleNotFoundError"**: Make sure all imports are in `requirements.txt`
- **Port issues**: Don't hardcode port - already fixed in app.py
- **Database resets**: Switch to PostgreSQL for persistent storage
- **View logs**: Check Render dashboard → Logs tab for errors

## After Deployment

```bash
# To make updates:
git add .
git commit -m "Your update message"
git push origin main
# Render will automatically rebuild and deploy!
```

# 🚀 Free Deployment Guide

## Option 1: Render (Recommended - 100% Free)

### Step 1: Create Render Account
1. Go to https://render.com/
2. Sign up with GitHub (free)
3. Connect your GitHub account

### Step 2: Create PostgreSQL Database (Free)
1. In Render dashboard → "New" → "PostgreSQL"
2. Name: `nymph-db`
3. Plan: **Free** (no credit card needed)
4. Click "Create Database"
5. **Save the connection details** (you'll need them)

### Step 3: Deploy Backend
1. In Render dashboard → "New" → "Web Service"
2. Connect to your `nymph-docker` repository
3. Configure:
   - **Name**: `nymph-backend`
   - **Root Directory**: `backend`
   - **Environment**: `Docker`
   - **Plan**: **Free**
   - **Port**: `8002`

4. **Environment Variables** (Add these):
   ```
   DATABASE_URL=<paste_from_step_2>
   OPENAI_API_KEY=your_openai_key
   VLM_API_KEY=your_vlm_key
   VLMRUN_API_KEY=your_vlm_key
   VLM_API_URL=https://api.vlm.run/v1/chat/completions
   PORT=8002
   ```

### Step 4: Deploy Frontend
1. In Render dashboard → "New" → "Static Site"
2. Connect to your `nymph-docker` repository
3. Configure:
   - **Name**: `nymph-frontend`
   - **Root Directory**: `frontend`
   - **Build Command**: `npm install && npm run build`
   - **Publish Directory**: `out`

4. **Environment Variables**:
   ```
   NEXT_PUBLIC_API_URL=https://nymph-backend.onrender.com
   ```

### Step 5: Test Your Live App!
- Frontend: `https://nymph-frontend.onrender.com`
- Backend: `https://nymph-backend.onrender.com`

---

## Option 2: Split Deployment (100% Free)

### Frontend: Vercel
1. Go to https://vercel.com/
2. Import your GitHub repo
3. Configure:
   - **Framework**: Next.js
   - **Root Directory**: `frontend`
   - **Environment Variable**: `NEXT_PUBLIC_API_URL=your_backend_url`

### Backend: Railway
1. Go to https://railway.app/
2. Deploy from GitHub
3. Add PostgreSQL service (free $5 credit)

---

## 🎯 Which Option Do You Want?

1. **Render** (easiest, everything in one place)
2. **Split deployment** (Vercel + Railway)
3. **Alternatives** (Supabase, PlanetScale, etc.)

Let me know which you prefer and I'll guide you through it step by step! 🚀

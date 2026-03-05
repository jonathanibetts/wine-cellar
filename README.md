# 🍷 Wine Cellar Manager

A Streamlit web app to manage your wine cellar with optimal drinking windows fetched from Wine-Searcher and other sources.

## Features
- Add wines with producer, name, vintage, region, format, quantity, price, and location
- Sortable, filterable table of your cellar
- 🔄 Refresh Drinking Windows button queries Wine-Searcher + Vivino + heuristics
- Colour-coded status: 🟢 Not ready | 🟡 Drink now | 🔴 Past peak
- Export cellar to CSV
- Cellar stats dashboard

## Deployment to Streamlit Cloud (free, public URL)

### Step 1: Create a GitHub repository
1. Go to [github.com](https://github.com) and create a new repository called `wine-cellar`
2. Upload `app.py` and `requirements.txt` to the repository

### Step 2: Deploy on Streamlit Cloud
1. Go to [share.streamlit.io](https://share.streamlit.io) and sign in with GitHub
2. Click **New app**
3. Select your `wine-cellar` repository, branch `main`, and file `app.py`
4. Click **Deploy** — your app will be live at a URL like:
   `https://yourusername-wine-cellar-app-xyz.streamlit.app`

### Step 3: Use the app
- Add your wines using the **Add a New Bottle** form
- Click **🔄 Refresh Drinking Windows** to fetch drinking window data
- Sort by Producer, Vintage, Region, etc.
- Colour coding shows at a glance what to drink now

## Local Development
```bash
pip install -r requirements.txt
streamlit run app.py
```

## Data Persistence
Wine data is saved in `wine_cellar.json` in the same directory.
For cloud deployment, consider replacing with a free database like Supabase or Airtable for true persistence.

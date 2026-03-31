# Nike Image Downloader — Guide de déploiement

## Architecture
- **Backend** : Python/Flask → hébergé sur Railway (gratuit)
- **Frontend** : HTML/CSS/JS → hébergé sur Vercel (gratuit)

---

## ÉTAPE 1 — Déployer le backend sur Railway

### 1.1 Créer un compte Railway
→ Va sur https://railway.app et connecte-toi avec GitHub

### 1.2 Mettre les fichiers backend sur GitHub
1. Crée un nouveau repo GitHub (ex: `nike-downloader-api`)
2. Mets ces 3 fichiers dedans :
   - `main.py`
   - `requirements.txt`
   - `Procfile`

### 1.3 Déployer sur Railway
1. Clique **"New Project"** → **"Deploy from GitHub repo"**
2. Sélectionne ton repo `nike-downloader-api`
3. Railway détecte automatiquement le `Procfile` et installe les dépendances
4. Attends ~2 minutes que le build finisse
5. Clique sur **"Settings"** → **"Domains"** → **"Generate Domain"**
6. Copie l'URL (ex: `https://nike-downloader-api.up.railway.app`)

---

## ÉTAPE 2 — Configurer le frontend

1. Ouvre `index.html`
2. Ligne 4 du script JS, remplace :
   ```
   const API_BASE = "https://TON-BACKEND.up.railway.app";
   ```
   par ton URL Railway :
   ```
   const API_BASE = "https://nike-downloader-api.up.railway.app";
   ```

---

## ÉTAPE 3 — Déployer le frontend sur Vercel

### Option A — Vercel (recommandé, 0 config)
1. Va sur https://vercel.com et connecte-toi avec GitHub
2. Crée un repo GitHub (ex: `nike-downloader-frontend`) avec `index.html` dedans
3. Dans Vercel : **"New Project"** → sélectionne ce repo
4. Clique **"Deploy"** — c'est tout
5. Vercel donne une URL publique (ex: `https://nike-downloader.vercel.app`)

### Option B — Netlify (alternative)
1. Va sur https://netlify.com
2. Glisse-dépose le fichier `index.html` directement sur la page
3. URL générée instantanément

---

## Résumé des URLs finales
| Service   | URL                                          |
|-----------|----------------------------------------------|
| Backend   | https://nike-downloader-api.up.railway.app   |
| Frontend  | https://nike-downloader.vercel.app           |

---

## Tester en local (optionnel)

```bash
# Backend
cd backend
pip install -r requirements.txt
python main.py
# → tourne sur http://localhost:8000

# Frontend
# Dans index.html, remplace API_BASE par "http://localhost:8000"
# Ouvre index.html dans le navigateur
```

---

## Notes
- Railway offre 500h/mois gratuitement (suffisant pour usage perso)
- Vercel est gratuit sans limite pour les sites statiques
- Les images téléchargées sont en résolution native (fl_original)

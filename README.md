# 📝 QuizAgent CI

Plateforme d'évaluation des agents de terrain — Streamlit + SQLite.

---

## Fonctionnalités

**Côté Agent (optimisé mobile)**
- Recherche par nom/prénom/matricule parmi les agents publiés
- Saisie du code du quiz → lancement immédiat
- Chronomètre en temps réel (vert → orange → rouge)
- Soumission automatique à la fin du temps
- 4 types de questions : Choix unique · Choix multiple · Numérique · Texte libre
- Page de résultat avec score et pourcentage

**Côté Admin (protégé par mot de passe)**
- Import agents : fichier CSV/Excel ou Google Sheets
- Publication/dépublication individuelle ou globale
- Création/modification/suppression de quiz avec éditeur de questions
- Consultation des résultats et export Excel formaté

---

## Déploiement

### Option A — Local (développement)

```bash
# 1. Cloner le projet
git clone https://github.com/<votre-compte>/quizagent-ci.git
cd quizagent-ci

# 2. Installer les dépendances
pip install -r requirements.txt

# 3. Configurer le mot de passe (copier le template)
cp .streamlit/secrets.toml .streamlit/secrets.toml   # déjà présent
# Éditez .streamlit/secrets.toml et changez ADMIN_PASSWORD

# 4. Lancer
streamlit run app.py
# → http://localhost:8501
```

---

### Option B — Docker (VPS, serveur local)

C'est l'option **recommandée en production** : la base SQLite est dans
un volume persistant et ne se perd jamais.

```bash
# Cloner + construire + lancer
git clone https://github.com/<votre-compte>/quizagent-ci.git
cd quizagent-ci

# Éditer le mot de passe dans docker-compose.yml (ADMIN_PASSWORD)

docker compose up -d
# → http://votre-ip:8501
```

**Mettre à jour l'application :**
```bash
git pull
docker compose up -d --build
```

**Sauvegarder la base de données :**
```bash
docker cp quizagent_ci:/app/data/quiz_app.db ./backup_$(date +%Y%m%d).db
```

---

### Option C — Render.com (gratuit, avec disque persistant)

1. Créez un compte sur [render.com](https://render.com)
2. **New → Web Service** → connectez votre dépôt GitHub
3. Paramètres :
   - **Environment :** Docker  
   - **Instance Type :** Free
4. Ajoutez un **Disk** :
   - Mount Path : `/app/data`
   - Size : 1 GB
5. **Environment Variables** :
   ```
   ADMIN_PASSWORD = VotreMotDePasseSecret
   APP_TITLE      = QuizAgent CI
   DB_PATH        = /app/data/quiz_app.db
   ```
6. Déployez → URL publique disponible en 3-4 minutes.

> ✅ Les données persistent même après redémarrage du serveur.

---

### Option D — Streamlit Community Cloud (gratuit, sans persistance)

> ⚠️ La base SQLite **se remet à zéro** à chaque redémarrage.  
> Adapté pour les **démonstrations et tests** uniquement.

1. Poussez le projet sur GitHub **sans `secrets.toml`** (il est dans `.gitignore`)
2. Allez sur [share.streamlit.io](https://share.streamlit.io) → *New app*
   - Repository : `votre-compte/quizagent-ci`
   - Branch : `main`
   - Main file : `app.py`
3. *Advanced settings → Secrets* — collez :
   ```toml
   ADMIN_PASSWORD = "VotreMotDePasseSecret"
   APP_TITLE      = "QuizAgent CI"
   ```
4. Déployez.

---

## Configuration

Toutes les valeurs se lisent dans l'ordre :  
`st.secrets` → variable d'environnement → valeur par défaut

| Clé | Défaut | Description |
|-----|--------|-------------|
| `ADMIN_PASSWORD` | `admin2026` | Mot de passe admin |
| `APP_TITLE` | `QuizAgent CI` | Titre affiché |
| `APP_SUBTITLE` | `Plateforme d'évaluation…` | Sous-titre |
| `ORG_NAME` | *(vide)* | Nom de l'organisation |
| `DB_PATH` | `data/quiz_app.db` | Chemin SQLite |

---

## Import des agents

### Fichier CSV / Excel
| Colonne | Noms acceptés |
|---------|---------------|
| Nom * | `nom`, `name`, `lastname` |
| Prénom | `prenom`, `prénom`, `firstname` |
| Matricule | `matricule`, `id`, `code` |

### Google Sheets
1. Ouvrez le classeur → **Partager → Toute personne avec le lien peut voir**
2. Copiez l'URL et collez-la dans *Admin → Agents → Importer*

> L'admin doit **publier** les agents après import pour qu'ils apparaissent dans la recherche.

---

## Workflow type

```
ADMIN                             AGENT
  ├─ Import agents                  │
  ├─ Publie les agents              │
  ├─ Crée quiz  (code : QZ001)      │
  ├─ Active le quiz                 │
  │                                 │
  │               Tape son nom →    │
  │               Sélectionne →     │
  │               Saisit QZ001 →    │
  │               Compose →         │
  │               Soumet →          │
  │                                 │
  ├─ Consulte les résultats         │
  └─ Exporte Excel                  │
```

---

## Structure du projet

```
quizagent_ci/
├── app.py                 # Interface Streamlit
├── database.py            # Couche données SQLite
├── config.py              # Configuration centralisée
├── requirements.txt
├── Dockerfile             # Image Docker
├── docker-compose.yml     # Déploiement Docker one-command
├── .gitignore
└── .streamlit/
    ├── config.toml        # Thème Streamlit
    └── secrets.toml       # ⚠️ Local uniquement, non commité
```

---

## Mot de passe par défaut

`admin2026` — **À changer avant tout déploiement public.**

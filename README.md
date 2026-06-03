# Seguridad V2

Sistema de vigilancia con login para padre/hijo, panel de bienvenida, camara de laptop, deteccion con modelo YOLOv8 ya entrenado, evidencias en Supabase Storage y rutas guardadas en PostgreSQL.

## Estructura

```txt
seguridad_v2/
  backend/
    app/
      config.py
      detector.py
      main.py
      supabase_client.py
    evidence/
    models/
      .gitkeep
    .env.example
    requirements.txt
  frontend/
    src/
      App.jsx
      main.jsx
      lib/
        supabase.js
      styles.css
    .env.example
    index.html
    package.json
    postcss.config.js
    tailwind.config.js
    vite.config.js
  supabase/
    schema.sql
  .gitignore
  README.md
```

## Comandos usados / instalacion

## Deploy

Para Vercel, despliega solo el frontend. Revisa la guia:

```txt
DEPLOYMENT_VERCEL.md
```

El backend con FastAPI, OpenCV, camara local y YOLO debe correr en un servidor persistente con HTTPS y acceso a la camara.

### Inicio recomendado

Desde la raiz del proyecto:

```powershell
.\start_project.ps1
```

Este script valida `.env`, cierra procesos viejos en `8001` y `5173`, inicia FastAPI y luego inicia React/Vite.

### 1. Backend

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
```

Coloca tu modelo entrenado en:

```txt
backend/models/best.pt
```

Edita `backend/.env` con tus datos de Supabase.

Ejecutar backend:

```powershell
uvicorn app.main:app --reload --host 127.0.0.1 --port 8001
```

### 2. Frontend

```powershell
cd frontend
npm install
copy .env.example .env
```

Edita `frontend/.env` con tus datos publicos de Supabase.

Ejecutar frontend:

```powershell
npm run dev
```

### 3. Supabase

Ejecuta el contenido de `supabase/schema.sql` en el SQL Editor de Supabase.

Crea un bucket privado llamado:

```txt
evidencias
```

## Flujo

1. Padre o hijo inicia sesion con Supabase Auth.
2. El frontend consulta `perfiles_usuarios` para obtener rol y nombre.
3. El panel muestra la camara de la laptop servida por FastAPI.
4. FastAPI usa OpenCV para leer la camara y YOLOv8 para detectar objetos.
5. Detecta las clases del modelo actual: persona, arma de fuego, arma blanca, pasamontana, mascarilla y casco.
6. Si detecta una alerta amarilla o roja, guarda evidencia en Supabase Storage, registra el evento y envia aviso por Telegram si esta habilitado.

## Variables importantes

Backend:

```env
SUPABASE_URL=
SUPABASE_SERVICE_ROLE_KEY=
SUPABASE_STORAGE_BUCKET=evidencias
MODEL_PATH=models/best.pt
CAMERA_INDEX=0
DETECTION_CONFIDENCE=0.45
SUSPICIOUS_LABELS=arma_de_fuego,arma_blanca,pasamontana,mascarilla,casco
```

Frontend:

```env
VITE_SUPABASE_URL=
VITE_SUPABASE_ANON_KEY=
VITE_API_URL=http://127.0.0.1:8001
```

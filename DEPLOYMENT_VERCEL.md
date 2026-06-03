# Deploy seguro en Vercel

Este proyecto debe desplegarse en dos partes:

1. **Frontend React/Vite en Vercel**.
2. **Backend FastAPI + OpenCV + YOLO en un servidor persistente** con acceso a la camara, por ejemplo VPS, Railway, Render, Fly.io o una maquina local expuesta por HTTPS.

El backend no se recomienda para Vercel porque usa camara local, procesos continuos, OpenCV, YOLO y un modelo `.pt`. Vercel Functions son serverless y no tienen acceso a la camara de tu laptop.

## Variables en Vercel

Configura solo estas variables publicas en el proyecto de Vercel:

```env
VITE_SUPABASE_URL=https://TU-PROYECTO.supabase.co
VITE_SUPABASE_ANON_KEY=TU_ANON_KEY_PUBLICA
VITE_API_URL=https://TU-BACKEND-PUBLICO.example.com
```

No pongas estas variables en Vercel para el frontend:

```env
SUPABASE_SERVICE_ROLE_KEY
TELEGRAM_BOT_TOKEN
SUPABASE_SERVICE_ROLE
```

Esas van solo en el servidor del backend.

## Configuracion de Vercel

El archivo `vercel.json` ya configura:

- instalacion desde `frontend/`
- build de Vite
- salida `frontend/dist`
- fallback para SPA
- headers de seguridad

La raiz del repo se puede importar en Vercel directamente.

## Backend en produccion

En el servidor del backend configura:

```env
SUPABASE_URL=https://TU-PROYECTO.supabase.co
SUPABASE_SERVICE_ROLE_KEY=TU_SERVICE_ROLE_KEY
SUPABASE_STORAGE_BUCKET=evidencias
FRONTEND_ORIGIN=https://TU-FRONTEND.vercel.app
TELEGRAM_ENABLED=true
TELEGRAM_BOT_TOKEN=TU_TOKEN_DE_BOTFATHER
TELEGRAM_BOT_USERNAME=TU_USUARIO_DEL_BOT
```

Si usas preview deployments de Vercel, puedes separar origenes con coma:

```env
FRONTEND_ORIGIN=https://TU-FRONTEND.vercel.app,https://TU-PREVIEW.vercel.app
```

## Checklist antes de subir a GitHub

- Verifica que `.env` no este versionado.
- No subas `backend/models/best.pt` si el modelo es privado.
- No subas tokens reales en README, issues, capturas o commits.
- Usa `VITE_` solo para valores publicos.
- Rota cualquier token que haya sido pegado en una conversacion, commit o captura.

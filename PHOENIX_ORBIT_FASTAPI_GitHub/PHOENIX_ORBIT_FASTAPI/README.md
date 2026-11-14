# PHOENIX ORBIT — FastAPI + Gemini

Backend RAG para consultar documentos PDF científicos.

## Ejecutar localmente (PowerShell)
Desde la carpeta `backend`:

```powershell
python -m venv venv
.\\venv\\Scripts\\Activate.ps1
pip install -r requirements.txt
$env:GEMINI_API_KEY="TU_CLAVE"
uvicorn main:app --reload
```

Abre `http://127.0.0.1:8000/docs`.

## Endpoints
- `GET /health`
- `GET /documents`
- `POST /documents` (PDF, campo `file`)
- `POST /chat` (JSON: `{"question":"¿Qué dice el documento?","top_k":5}`)

## GitHub y despliegue
Sube este proyecto al repositorio GitHub. GitHub almacena el código; no ejecuta FastAPI.
`render.yaml` permite desplegarlo en Render. Configura `GEMINI_API_KEY` como secreto y `FRONTEND_ORIGINS` con el dominio real de la web.

## Conectar frontend
Envía `POST https://TU-API.onrender.com/chat` con JSON:
`{"question":"¿Qué estudia el experimento?","top_k":5}`.

## Limitaciones
Extrae texto de PDF; escaneados requieren OCR. No descarga automáticamente enlaces ni transcribe videos. El índice JSON local puede perderse en hosting efímero. Añade autenticación antes de permitir cargas públicas y configura CORS para el dominio real.

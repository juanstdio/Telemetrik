from fastapi import FastAPI, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
import uvicorn
import os
import time
import typing as t

# ----------------------------------------------------
# Configuración y Estado Global
# ----------------------------------------------------

# Define la ruta al directorio 'static'
STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")

# Almacenamiento global de eventos.
EVENT_QUEUE: t.List[t.Dict[str, t.Any]] = []

# Configuración de códigos de estado y colores base.
# IMPORTANTE: Usamos nombres o valores CSS válidos aquí (ej: 'purple', '#800080')
STATUS_CONFIG = {
    200: "green",    # Solicitud exitosa
    404: "red",      # Recurso no encontrado
    500: "yellow",   # Error interno del servidor
    303: "blue",     # Ver otros
}

# ----------------------------------------------------
# Inicialización de la Aplicación
# ----------------------------------------------------
app = FastAPI(
    title="Visualizador de Actividad Web",
    description="Backend para generar, distribuir y configurar eventos de partículas.",
    version="1.1.0"
)

# Monta el directorio estático.
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# ----------------------------------------------------
# Pydantic Modelos (Para Swagger UI)
# ----------------------------------------------------

class CodeConfig(BaseModel):
    """Esquema para configurar un nuevo código de estado y color."""
    code: int
    color: str
    
    class Config:
        # Ejemplo para Swagger UI
        schema_extra = {
            "example": {
                "code": 418,
                "color": "hotpink"
            }
        }

# ----------------------------------------------------
# Rutas API
# ----------------------------------------------------

@app.get("/")
async def root():
    """Redirige la ruta raíz al visualizador estático."""
    return RedirectResponse(url="/static/index.html")

# Endpoint original para generar eventos 
@app.get("/api/{status_code}")
async def generate_event(status_code: int):
    """
    Endpoint para generar un evento de partícula.
    Almacena el evento en la cola global.
    """
    # Usar get() para manejar códigos que puedan no existir si el endpoint es llamado directamente
    color = STATUS_CONFIG.get(status_code)

    if not color:
        return {"message": f"Código {status_code} no configurado para visualización. Añádalo en /api/config/add_code."}

    print(f"[{status_code}] Evento generado: color={color}")

    # Almacenar el evento en la cola con un timestamp
    EVENT_QUEUE.append({
        "status_code": status_code,
        "color": color,
        "timestamp": time.time()
    })

    return {"message": "Evento registrado", "status_code": status_code, "color": color}

# ----------------------------------------------------
# NUEVO ENDPOINT DE CONFIGURACIÓN
# ----------------------------------------------------

@app.post("/api/config/add_code")
async def add_custom_code(config: CodeConfig):
    """
    🎯 Agrega o actualiza un nuevo código de estado y su color asociado.
    El color debe ser un nombre CSS válido (ej: 'purple', 'orange', '#ff0000').
    """
    global STATUS_CONFIG
    
    # Asegurarse de que el color sea string y el código sea int
    code = config.code
    color = config.color.lower().strip() # Normalizar color
    
    STATUS_CONFIG[code] = color
    
    return {
        "message": f"Código {code} añadido/actualizado con color '{color}'.",
        "active_codes": STATUS_CONFIG
    }

# ----------------------------------------------------
# Endpoint de Polling
# ----------------------------------------------------

@app.get("/api/events/poll")
async def poll_events():
    """
    Endpoint de Polling: Devuelve todos los eventos acumulados y luego vacía la cola.
    """
    global EVENT_QUEUE

    # 1. Copiar la cola actual de eventos.
    events_to_send = list(EVENT_QUEUE)

    # 2. Vaciar la cola global.
    EVENT_QUEUE = []

    return {"events": events_to_send}


# ----------------------------------------------------
# Ejecución del Servidor
# ----------------------------------------------------

if __name__ == "__main__":
    print("Accede a la documentación interactiva (Swagger UI) en: /docs")
    print("  - Partícula Verde (200): http://127.0.0.1:8000/api/200")
    print("  - Configurar nuevo código: POST http://127.0.0.1:8000/api/config/add_code")

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True, log_config=None )

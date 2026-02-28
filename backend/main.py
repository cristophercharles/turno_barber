from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from .database import engine
from .models import Base
from .routes import turnos, cliente

app = FastAPI(title="Turno Barber 💈")

# =========================
# ARCHIVOS ESTÁTICOS
# =========================
app.mount("/static", StaticFiles(directory="static"), name="static")

# =========================
# BASE DE DATOS
# =========================
Base.metadata.create_all(bind=engine)

# =========================
# CORS
# =========================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =========================
# RUTAS API
# =========================
app.include_router(turnos.router, prefix="/turnos", tags=["Turnos"])
app.include_router(cliente.router, prefix="/cliente", tags=["Cliente"])

# =========================
# ROOT
# =========================
@app.get("/")
def root():
    return {"status": "Sistema de turnos activo 💈"}

# =========================
# TV
# =========================
@app.get("/tv", response_class=HTMLResponse)
def ver_tv():
    with open("frontend/tv.html", encoding="utf-8") as f:
        return f.read()

# =========================
# CLIENTE
# =========================
@app.get("/cliente_app", response_class=HTMLResponse)
def ver_cliente():
    with open("frontend/cliente.html", encoding="utf-8") as f:
        return f.read()

# =========================
# BARBERO
# =========================
@app.get("/barbero", response_class=HTMLResponse)
def ver_barbero():
    with open("static/index.html", encoding="utf-8") as f:
        return f.read()

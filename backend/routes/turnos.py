from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from datetime import datetime, date

from backend.database import get_db
from backend.models import Barbero, Turno, Cliente, Jornada

router = APIRouter()

# =========================
# UTIL
# =========================
def obtener_jornada_activa(db: Session):
    jornada = db.query(Jornada).filter(Jornada.activa == True).first()
    if not jornada:
        raise HTTPException(status_code=400, detail="No hay jornada activa")
    return jornada

# =========================
# JORNADA
# =========================
@router.post("/crear_jornada")
def crear_jornada(inicio: str, fin: str, db: Session = Depends(get_db)):
    hoy = date.today().isoformat()
    db.query(Jornada).filter(Jornada.activa == True).update({"activa": False})
    db.commit()

    jornada = Jornada(
        fecha=hoy,
        hora_inicio=inicio,
        hora_fin=fin,
        activa=True
    )
    db.add(jornada)
    db.commit()
    return {"mensaje": "Jornada creada correctamente"}

@router.get("/jornada")
def obtener_jornada(db: Session = Depends(get_db)):
    jornada = obtener_jornada_activa(db)
    return {
        "fecha": jornada.fecha,
        "inicio": jornada.hora_inicio,
        "fin": jornada.hora_fin
    }

# =========================
# BARBEROS
# =========================
@router.post("/agregar_barbero")
def agregar_barbero(nombre: str, silla: str, duracion: int, db: Session = Depends(get_db)):
    jornada = obtener_jornada_activa(db)
    existe = db.query(Barbero).filter(
        Barbero.silla == silla,
        Barbero.jornada_id == jornada.id
    ).first()
    if existe:
        raise HTTPException(status_code=400, detail="La silla ya tiene barbero")

    barbero = Barbero(
        nombre=nombre,
        silla=silla,
        duracion=duracion,
        jornada_id=jornada.id
    )
    db.add(barbero)
    db.commit()
    return {"mensaje": "Barbero agregado"}

@router.get("/barberos")
def obtener_barberos(db: Session = Depends(get_db)):
    jornada = obtener_jornada_activa(db)
    barberos = db.query(Barbero).filter(Barbero.jornada_id == jornada.id).all()
    return {
        "barberos": [
            {"id": b.id, "nombre": b.nombre, "silla": b.silla, "duracion": b.duracion}
            for b in barberos
        ]
    }

# =========================
# TURNOS
# =========================
@router.post("/registrar")
def registrar_turno(nombre: str, hora: str, barbero_id: int, db: Session = Depends(get_db)):
    jornada = obtener_jornada_activa(db)

    barbero = db.query(Barbero).filter(
        Barbero.id == barbero_id,
        Barbero.jornada_id == jornada.id
    ).first()
    if not barbero:
        raise HTTPException(status_code=400, detail="Barbero no encontrado")

    # 🔒 BLOQUEAR SI LA HORA YA ESTÁ OCUPADA (cliente o barbero)
    ocupado = db.query(Turno).filter(
        Turno.barbero_id == barbero.id,
        Turno.jornada_id == jornada.id,
        Turno.hora == hora,
        Turno.estado != "finalizado"
    ).first()
    if ocupado:
        raise HTTPException(status_code=400, detail="Hora no disponible")

    # Crear cliente
    cliente = Cliente(nombre=nombre)
    db.add(cliente)
    db.commit()
    db.refresh(cliente)

    # ✅ NÚMERO REAL POR BARBERO + JORNADA
    ultimo = db.query(Turno).filter(
        Turno.barbero_id == barbero.id,
        Turno.jornada_id == jornada.id
    ).order_by(Turno.numero.desc()).first()

    numero = ultimo.numero + 1 if ultimo else 1

    turno = Turno(
        numero=numero,
        fecha=jornada.fecha,
        cliente_id=cliente.id,
        barbero_id=barbero.id,
        jornada_id=jornada.id,
        hora=hora,
        estado="esperando"
    )

    db.add(turno)
    db.commit()
    db.refresh(turno)

    # ❌ YA NO SE AUTO-ATIENDE
    # ✔️ SOLO EL BOTÓN /atender CAMBIA EL ESTADO

    return {
        "mensaje": "Turno registrado",
        "numero": turno.numero,
        "estado": turno.estado
    }

@router.get("/todos")
def obtener_todos_turnos(db: Session = Depends(get_db)):
    jornada = obtener_jornada_activa(db)
    turnos = db.query(Turno).filter(Turno.fecha == jornada.fecha).order_by(Turno.hora).all()
    return {
        "turnos": [
            {
                "id": t.id,
                "numero": t.numero,
                "hora": t.hora,
                "estado": t.estado,
                "cliente": t.cliente.nombre,
                "barbero": t.barbero.nombre,
                "barbero_id": t.barbero.id,
                "silla": t.barbero.silla
            }
            for t in turnos
        ]
    }


# ===== ATENDER TURNO (BOTÓN BARBERO)
@router.post("/atender")
def atender_turno(turno_id: int, db: Session = Depends(get_db)):
    turno = db.query(Turno).filter(Turno.id == turno_id).first()
    if not turno:
        raise HTTPException(status_code=404, detail="Turno no encontrado")

    jornada = obtener_jornada_activa(db)

    # Finalizar turno activo previo del mismo barbero
    turno_activo = db.query(Turno).filter(
        Turno.barbero_id == turno.barbero_id,
        Turno.fecha == jornada.fecha,
        Turno.estado == "atendiendo"
    ).first()

    if turno_activo:
        turno_activo.estado = "finalizado"
        turno_activo.fin_real = datetime.now()

    # Pasar este turno a atención
    turno.estado = "atendiendo"
    turno.inicio_real = datetime.now()

    db.commit()
    db.refresh(turno)

    return {"mensaje": "Turno en atención"}

# ===== FINALIZAR POR ID DEL TURNO
@router.post("/finalizar")
def finalizar_turno(turno_id: int, db: Session = Depends(get_db)):
    turno = db.query(Turno).filter(Turno.id == turno_id).first()
    if not turno:
        raise HTTPException(status_code=400, detail="Turno no encontrado")

    turno.estado = "finalizado"
    turno.fin_real = datetime.now()

    siguiente = db.query(Turno).filter(
        Turno.barbero_id == turno.barbero_id,
        Turno.fecha == turno.fecha,
        Turno.estado == "esperando"
    ).order_by(Turno.hora).first()

    if siguiente:
        siguiente.estado = "atendiendo"
        siguiente.inicio_real = datetime.now()

    db.commit()
    return {"mensaje": "Turno finalizado"}

# ===== LIBERAR TURNO POR NUMERO
@router.post("/liberar")
def liberar_turno(barbero_id: int, hora: str, numero: int, db: Session = Depends(get_db)):
    turno = db.query(Turno).filter(
        Turno.barbero_id == barbero_id,
        Turno.hora == hora,
        Turno.numero == numero,
        Turno.estado != "finalizado"
    ).first()

    if not turno:
        raise HTTPException(status_code=400, detail="Turno no encontrado")

    turno.estado = "esperando"
    turno.inicio_real = None
    turno.fin_real = None
    db.commit()
    return {"mensaje": f"Turno #{numero} liberado"}

# =========================
# TV
# =========================
@router.get("/tv")
def turnos_tv(db: Session = Depends(get_db)):
    jornada = obtener_jornada_activa(db)

    turnos = db.query(Turno).filter(
        Turno.fecha == jornada.fecha,
        Turno.estado != "finalizado"
    ).order_by(Turno.hora).all()

    ahora = datetime.now()
    actuales = []
    siguientes = []

    for t in turnos:
        duracion = t.barbero.duracion
        restante = duracion

        if t.estado == "atendiendo" and t.inicio_real:
            transcurrido = int((ahora - t.inicio_real).total_seconds() / 60)
            restante = max(duracion - transcurrido, 0)

        data = {
            "turno_id": t.id,               # 🔊 nuevo
            "numero": t.numero,
            "cliente": t.cliente.nombre,
            "hora": t.hora,
            "barbero": t.barbero.nombre,
            "silla": t.barbero.silla,
            "duracion": duracion,           # 🔊 nuevo
            "restante": restante,
            "porcentaje": int(((duracion - restante) / duracion) * 100) if duracion else 0,
            "estado": t.estado
        }

        if t.estado == "atendiendo":
            actuales.append(data)
        else:
            siguientes.append(data)

    return {
        "actual": actuales,
        "siguientes": siguientes
    }


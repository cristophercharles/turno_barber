from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from datetime import datetime, timedelta, date
from backend.database import get_db
from backend.models import Barbero, Turno, Cliente, Jornada

router = APIRouter(tags=["Cliente"])

# =========================
# OBTENER JORNADA ACTIVA
# =========================
def obtener_jornada_activa(db: Session):
    jornada = db.query(Jornada).filter(Jornada.activa == True).first()
    if not jornada:
        raise HTTPException(status_code=400, detail="No hay jornada activa")
    return jornada

# =========================
# HORAS DISPONIBLES
# =========================
@router.get("/horas")
def horas_disponibles(barbero_id: int, db: Session = Depends(get_db)):
    jornada = obtener_jornada_activa(db)

    barbero = db.query(Barbero).filter(
        Barbero.id == barbero_id,
        Barbero.jornada_id == jornada.id
    ).first()
    if not barbero:
        raise HTTPException(status_code=404, detail="Barbero no encontrado")

    ocupadas = {
        t.hora for t in db.query(Turno).filter(
            Turno.barbero_id == barbero.id,
            Turno.jornada_id == jornada.id,
            Turno.estado != "finalizado"
        ).all()
    }

    h_inicio = datetime.strptime(jornada.hora_inicio, "%H:%M")
    h_fin = datetime.strptime(jornada.hora_fin, "%H:%M")

    horas = []
    actual = h_inicio
    while actual < h_fin:
        hora_str = actual.strftime("%H:%M")
        if hora_str not in ocupadas:
            horas.append(hora_str)
        actual += timedelta(minutes=barbero.duracion)

    return {"horas": horas}

# =========================
# REGISTRAR TURNO
# =========================
@router.post("/registrar")
def registrar_turno(
    nombre: str,
    hora: str,
    barbero_id: int,
    db: Session = Depends(get_db)
):
    jornada = obtener_jornada_activa(db)

    barbero = db.query(Barbero).filter(
        Barbero.id == barbero_id,
        Barbero.jornada_id == jornada.id
    ).first()
    if not barbero:
        raise HTTPException(status_code=400, detail="Barbero no encontrado")

    ocupado = db.query(Turno).filter(
        Turno.barbero_id == barbero.id,
        Turno.jornada_id == jornada.id,
        Turno.hora == hora,
        Turno.estado != "finalizado"
    ).first()
    if ocupado:
        raise HTTPException(status_code=400, detail="Hora no disponible")

    cliente = Cliente(nombre=nombre)
    db.add(cliente)
    db.commit()
    db.refresh(cliente)

    ultimo = db.query(Turno).filter(
        Turno.barbero_id == barbero.id,
        Turno.jornada_id == jornada.id
    ).order_by(Turno.numero.desc()).first()

    numero = ultimo.numero + 1 if ultimo else 1

    turno = Turno(
        cliente_id=cliente.id,
        barbero_id=barbero.id,
        jornada_id=jornada.id,
        numero=numero,
        hora=hora,
        estado="esperando",
        fecha=date.today()
    )

    db.add(turno)
    db.commit()
    db.refresh(turno)

    return {
        "turno": {
            "id": turno.id,
            "hora": turno.hora,
            "estado": turno.estado
        }
    }

# =========================
# ESTADO DEL TURNO CLIENTE
# =========================
@router.get("/estado")
def estado_turno(turno_id: int, db: Session = Depends(get_db)):
    turno = db.query(Turno).filter(Turno.id == turno_id).first()

    # 🔴 si ya no existe → cerrado
    if not turno:
        return {"cerrado": True}

    if turno.estado == "finalizado":
        return {"cerrado": True}

    barbero = turno.barbero
    duracion = barbero.duracion

    cola = db.query(Turno).filter(
        Turno.barbero_id == turno.barbero_id,
        Turno.jornada_id == turno.jornada_id,
        Turno.estado != "finalizado"
    ).order_by(Turno.numero).all()

    posicion = cola.index(turno)
    ahora = datetime.now()

    if turno.estado == "atendiendo" and turno.inicio_real:
        transcurrido = (ahora - turno.inicio_real).total_seconds() / 60
        restante = max(0, duracion - int(transcurrido))
    else:
        restante = posicion * duracion

    return {
        "cerrado": False,
        "estado": turno.estado,
        "hora": turno.hora,
        "personas_delante": posicion,
        "faltan_minutos": restante
    }

# =========================
# CANCELAR TURNO
# =========================
@router.post("/cancelar")
def cancelar_turno(turno_id: int, db: Session = Depends(get_db)):
    turno = db.query(Turno).filter(Turno.id == turno_id).first()
    if not turno:
        return {"mensaje": "Turno ya cancelado"}

    db.delete(turno)
    db.commit()

    return {"mensaje": "Turno cancelado"}

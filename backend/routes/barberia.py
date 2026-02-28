# app/routes/barbero.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import Turno


from backend.database import SessionLocal
from backend.models import Barberia

def validar_barberia(barberia_id: str):
    db = SessionLocal()
    barberia = db.query(Barberia).filter(
        Barberia.id == barberia_id,
        Barberia.activa == True
    ).first()
    db.close()
    return barberia

router = APIRouter(prefix="/barbero", tags=["Barbero"])

@router.post("/turnos")
def agregar_turno(nombre_cliente: str, db: Session = Depends(get_db)):
    turno = Turno(cliente=nombre_cliente)
    db.add(turno)
    db.commit()
    db.refresh(turno)
    return turno

@router.put("/turnos/{turno_id}/siguiente")
def siguiente_turno(turno_id: int, db: Session = Depends(get_db)):
    # Marcar turno actual como terminado
    turno = db.query(Turno).filter(Turno.id == turno_id).first()
    if not turno:
        raise HTTPException(status_code=404, detail="Turno no encontrado")
    turno.estado = "terminado"
    db.commit()
    
    # Retornar el siguiente turno en espera
    siguiente = db.query(Turno).filter(Turno.estado == "esperando").order_by(Turno.creado).first()
    if siguiente:
        siguiente.estado = "atendiendo"
        db.commit()
        return {"actual": siguiente}
    return {"message": "No hay más turnos en espera"}
    
@router.get("/turnos/tv")
def turnos_tv(db: Session = Depends(get_db)):
    actual = db.query(Turno).filter(Turno.estado == "atendiendo").order_by(Turno.creado).first()
    siguientes = db.query(Turno).filter(Turno.estado == "esperando").order_by(Turno.creado).all()
    return {"actual": actual, "siguientes": siguientes}

from backend.database import SessionLocal
from backend.models import Barberia

def validar_barberia(barberia_id: str):
    db = SessionLocal()
    barberia = db.query(Barberia).filter(
        Barberia.id == barberia_id,
        Barberia.activa == True
    ).first()
    db.close()
    return barberia

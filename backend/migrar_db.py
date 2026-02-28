from backend.database import SessionLocal
from backend.models import Barberia

db = SessionLocal()

barberia = Barberia(
    id="ABR-001",
    nombre="Alexander Barbería",
    licencia_key="TB-AX-001",
    pantallas_tv=1,
    activa=True
)

db.add(barberia)
db.commit()
db.close()

print("Barbería creada correctamente")

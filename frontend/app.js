const API_URL = "http://127.0.0.1:8000/turnos";

// 🟢 Cargar horarios disponibles
async function cargarHorariosDisponibles() {
    try {
        const res = await fetch(`${API_URL}/horarios_disponibles`);
        const data = await res.json();
        const select = document.getElementById("horaTurno");
        select.innerHTML = "";

        if (data.disponibles.length === 0) {
            const option = document.createElement("option");
            option.value = "";
            option.text = "No hay horas disponibles";
            select.appendChild(option);
            return;
        }

        data.disponibles.forEach(hora => {
            const option = document.createElement("option");
            option.value = hora;
            option.text = hora;
            select.appendChild(option);
        });
    } catch (err) {
        console.error(err);
    }
}

// 🟢 Agregar turno
async function agregarTurno() {
    const nombre = document.getElementById("nombreCliente").value.trim();
    const hora = document.getElementById("horaTurno").value;

    if (!nombre) return alert("Ingresa un nombre");
    if (!hora) return alert("Selecciona una hora");

    try {
        const res = await fetch(`${API_URL}/registrar?nombre=${encodeURIComponent(nombre)}&hora=${hora}`, {
            method: "POST"
        });
        const data = await res.json();

        if (res.status !== 200) {
            return alert(data.detail || "No se pudo registrar el turno");
        }

        document.getElementById("nombreCliente").value = "";
        cargarTurnos();
        cargarHorariosDisponibles(); // actualizar horas disponibles
    } catch (err) {
        console.error(err);
        alert("Error al agregar el turno");
    }
}

// 🔄 Cargar turnos y actualizar la UI
async function cargarTurnos() {
    try {
        const res = await fetch(`${API_URL}/tv`);
        const data = await res.json();

        const actualDiv = document.getElementById("turnoActual");
        const lista = document.getElementById("listaTurnos");
        lista.innerHTML = "";

        if (!data.actual) {
            actualDiv.innerHTML = "No hay turnos";
            actualDiv.style.background = "";
            return;
        }

        actualDiv.innerHTML = `#${data.actual.numero} - ${data.actual.nombre} <br> Hora: ${data.actual.hora} <br> Estado: ${data.actual.estado}`;
        actualDiv.style.background = data.actual.estado === "atendiendo" ? "#1e7f43" : "";

        data.siguientes.forEach(t => {
            const li = document.createElement("li");
            li.innerText = `#${t.numero} - ${t.nombre} (Hora: ${t.hora}, Estado: ${t.estado})`;
            lista.appendChild(li);
        });
    } catch (err) {
        console.error(err);
    }
}

// 🔹 Finalizar turno
async function finalizarTurno() {
    try {
        const res = await fetch(`${API_URL}/finalizar`, { method: "POST" });
        const data = await res.json();
        alert(data.mensaje);
        cargarTurnos();
        cargarHorariosDisponibles();
    } catch (err) {
        console.error(err);
    }
}

// 🔹 Liberar turno manual
async function liberarTurno() {
    const numero = parseInt(prompt("Ingresa el número del turno a liberar:"));
    if (!numero) return;

    try {
        const res = await fetch(`${API_URL}/liberar?numero=${numero}`, { method: "POST" });
        const data = await res.json();
        if (res.status !== 200) alert(data.detail);
        else alert(data.mensaje);
        cargarTurnos();
        cargarHorariosDisponibles();
    } catch (err) {
        console.error(err);
    }
}

// Eventos de botones
document.getElementById("btnAgregar")?.addEventListener("click", agregarTurno);
document.getElementById("btnFinalizar")?.addEventListener("click", finalizarTurno);
document.getElementById("btnLiberar")?.addEventListener("click", liberarTurno);

// Actualizar cada 3 segundos
setInterval(cargarTurnos, 3000);
cargarTurnos();
cargarHorariosDisponibles();

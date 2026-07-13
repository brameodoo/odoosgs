(function () {
    "use strict";

    console.log("Archivo route_map.js cargado exitosamente.");

    // =========================================================
    // 1. LÓGICA DE FILTRADO DE SELECTORES (DELEGACIÓN)
    // Se registra de inmediato para que funcione en cualquier momento
    // =========================================================
    document.addEventListener("change", async function (e) {
        if (e.target && e.target.id === "ruta_maestra_id") {
            const maestraId = e.target.value;
            const origenSelect = document.getElementById("nodo_origen_id");
            const destinoSelect = document.getElementById("nodo_destino_id");

            console.log("Cambio en Ruta Maestra detectado. ID:", maestraId);

            if (!maestraId || !origenSelect || !destinoSelect) return;

            try {
                // Fetch estándar compatible con type='http'
                const response = await fetch(`/get_nodos_by_maestra/${maestraId}`);
                if (!response.ok) return;

                const result = await response.json();

                // Llenar Origen
                origenSelect.innerHTML = '<option value="">-- Seleccione salida --</option>';
                result.origenes.forEach(n => {
                    let opt = document.createElement('option');
                    opt.value = n.id;
                    opt.textContent = n.name;
                    origenSelect.appendChild(opt);
                });

                // Llenar Destino
                destinoSelect.innerHTML = '<option value="">-- Seleccione llegada --</option>';
                result.destinos.forEach(n => {
                    let opt = document.createElement('option');
                    opt.value = n.id;
                    opt.textContent = n.name;
                    destinoSelect.appendChild(opt);
                });

                // Desbloqueo físico de campos
                origenSelect.disabled = false;
                destinoSelect.disabled = false;
                origenSelect.removeAttribute('disabled');
                destinoSelect.removeAttribute('disabled');
                
                console.log("Selectores de nodos actualizados y habilitados.");

            } catch (err) {
                console.error("Error en el filtrado de nodos:", err);
            }
        }
    });

    function bindSecurityLevelWidgets() {
        const widgets = document.querySelectorAll("[data-security-level-widget]");
        if (!widgets.length) return;

        const levelData = {
            1: {
                badge: "🟢 Básico",
                title: "Nivel 1 — Básico",
                description: "Ideal para operaciones estándar donde el usuario necesita una decisión rápida sin perder claridad.",
                items: [
                    "🚗 1 vehículo de custodia",
                    "👤 1 custodio",
                    "🔒 Candado mecánico",
                    "📍 GPS activo",
                    "⏱️ Cobertura estimada: 3 horas"
                ]
            },
            2: {
                badge: "🔵 Intermedio",
                title: "Nivel 2 — Intermedio",
                description: "Incrementa la cobertura para rutas con exposición media o necesidades adicionales de acompañamiento.",
                items: [
                    "🚗 Custodia principal + vehículo sombra",
                    "👥 2 custodios",
                    "🔒 Candado digital",
                    "📍 GPS activo",
                    "⏱️ Cobertura estimada: 4 horas"
                ]
            },
            3: {
                badge: "🟠 Avanzado",
                title: "Nivel 3 — Avanzado",
                description: "Recomendado para operaciones sensibles que requieren más presencia operativa y control en ruta.",
                items: [
                    "🚗 Custodia + sombra",
                    "👥 3 personas (incluye a bordo)",
                    "🔒 Candado digital",
                    "📍 GPS activo",
                    "⏱️ Cobertura estimada: 5 horas"
                ]
            },
            4: {
                badge: "🔴 Máximo",
                title: "Nivel 4 — Máximo",
                description: "Máxima cobertura para eventos críticos, alto riesgo o requerimientos corporativos reforzados.",
                items: [
                    "🚗 Custodia + sombra + a bordo",
                    "🚧 4 puntos de seguridad",
                    "👥 7 personas",
                    "🔒 Candado digital",
                    "📍 GPS activo",
                    "⏱️ Cobertura estimada: 6 horas"
                ]
            },
            '4x': {
                badge: "🛡️ Excepción",
                title: "Excepción + Nivel 4",
                description: "Escenario especial para solicitudes fuera de política estándar que requieren validación y operación reforzada.",
                items: [
                    "🔴 Basado en nivel 4",
                    "📋 Revisión especial de operación",
                    "👥 Recursos reforzados según evento",
                    "📍 GPS activo y monitoreo dedicado",
                    "☎️ Coordinación puntual con planeación"
                ]
            }
        };

        const renderWidget = (widget, level) => {
            const badge = widget.querySelector("[data-level-badge]");
            const title = widget.querySelector("[data-security-level-title]");
            const description = widget.querySelector("[data-security-level-description]");
            const content = widget.querySelector("[data-security-level-content]");
            if (!levelData[level]) {
                if (badge) badge.textContent = "Selecciona un nivel";
                if (title) title.textContent = "Nivel de Seguridad";
                if (description) description.textContent = "Elige una opción para ver el alcance del servicio y tomar una decisión con mayor claridad.";
                if (content) content.innerHTML = '<div class="text-muted">Aquí verás un resumen dinámico de vehículos, custodios, candados, GPS y cobertura estimada.</div>';
                return;
            }
            const summary = levelData[level];
            if (badge) badge.textContent = summary.badge;
            if (title) title.textContent = summary.title;
            if (description) description.textContent = summary.description;
            if (content) {
                content.innerHTML = `<ul>${summary.items.map((item) => `<li>${item}</li>`).join("")}</ul>`;
            }
        };

        widgets.forEach((widget) => {
            const radios = widget.querySelectorAll('input[name="nivel_seguridad"]');
            if (!radios.length) return;

            const selected = Array.from(radios).find((radio) => radio.checked);
            renderWidget(widget, selected ? selected.value : null);

            radios.forEach((radio) => {
                radio.addEventListener("change", () => renderWidget(widget, radio.value));
            });
        });
    }

    function showFeedback(element, type, message) {
        if (!element) return;
        element.className = `alert alert-${type} mb-3`;
        element.textContent = message;
        element.classList.remove("d-none");
    }

    function bindServiceControls() {
        const controlPanel = document.getElementById("service-control-panel");
        if (!controlPanel) return;

        const feedback = document.getElementById("service-control-feedback");
        const serviceId = controlPanel.dataset.serviceId;
        const token = controlPanel.dataset.token;
        const buttons = controlPanel.querySelectorAll(".service-action-btn");
        const horaLlegada = document.getElementById("hora-llegada");
        const diffLlegada = document.getElementById("diff-llegada");
        const horaInicio = document.getElementById("hora-inicio-real");
        const diffInicio = document.getElementById("diff-inicio");
        const stateBadge = document.querySelector(".badge.bg-info");

        buttons.forEach((button) => {
            button.addEventListener("click", async () => {
                if (button.disabled) return;
                const action = button.dataset.action;
                button.disabled = true;
                try {
                    const response = await fetch(`/custodia/service/${serviceId}/${action}`, {
                        method: "POST",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify({ params: { access_token: token } }),
                    });
                    const payload = await response.json();
                    const result = payload.result || payload;
                    if (result.status !== "success") {
                        showFeedback(feedback, "danger", result.message || "No fue posible registrar la acción.");
                        button.disabled = false;
                        return;
                    }

                    showFeedback(feedback, "success", result.message || "Registro actualizado correctamente.");
                    if (action === "llegada") {
                        if (horaLlegada) horaLlegada.textContent = result.hora_llegada || "Registrada";
                        if (diffLlegada) diffLlegada.textContent = result.diff_llegada_min ?? "0";
                        const startButton = controlPanel.querySelector('[data-action="iniciar"]');
                        if (startButton) startButton.disabled = false;
                    }
                    if (action === "iniciar") {
                        if (horaInicio) horaInicio.textContent = result.hora_inicio_real || "Registrada";
                        if (diffInicio) diffInicio.textContent = result.diff_inicio_min ?? "0";
                        if (stateBadge && result.state_label) stateBadge.textContent = result.state_label;
                    }
                } catch (error) {
                    console.error("Error al ejecutar acción de servicio:", error);
                    showFeedback(feedback, "danger", "Ocurrió un error de comunicación con el portal.");
                    button.disabled = false;
                }
            });
        });
    }

    function bindIncidentReporter() {
        const panel = document.getElementById("incident-panel");
        if (!panel) return;

        const serviceId = panel.dataset.serviceId;
        const token = panel.dataset.token;
        const textarea = document.getElementById("incident-message");
        const submit = document.getElementById("incident-submit");
        const feedback = document.getElementById("incident-feedback");

        if (!textarea || !submit) return;

        submit.addEventListener("click", async () => {
            const mensaje = textarea.value.trim();
            if (!mensaje) {
                showFeedback(feedback, "warning", "Debes describir la incidencia antes de enviarla.");
                return;
            }

            submit.disabled = true;
            try {
                const response = await fetch(`/custodia/service/${serviceId}/incidencia`, {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ params: { mensaje, access_token: token } }),
                });
                const payload = await response.json();
                const result = payload.result || payload;
                if (result.status !== "success") {
                    showFeedback(feedback, "danger", result.message || "No fue posible registrar la incidencia.");
                    submit.disabled = false;
                    return;
                }

                textarea.value = "";
                showFeedback(feedback, "success", result.message || "Incidencia reportada correctamente.");
            } catch (error) {
                console.error("Error al reportar incidencia:", error);
                showFeedback(feedback, "danger", "Ocurrió un error de comunicación con el portal.");
                submit.disabled = false;
                return;
            }
            submit.disabled = false;
        });
    }

    // =========================================================
    // 2. ARRANCAR MAPAS AL CARGAR LA PÁGINA
    // =========================================================
    function bootMaps() {
        console.log("DOM listo - Verificando existencia de mapas...");

        bindSecurityLevelWidgets();
        bindServiceControls();
        bindIncidentReporter();

        // Espera activa por Leaflet: en algunos entornos externos tarda en estar disponible.
        waitForLeaflet(15, 300, function () {
            const routeMapContainer = document.getElementById("route-map");
            const liveMapContainer = document.getElementById("live-map");

            if (routeMapContainer) {
                console.log("Iniciando Mapa de Ruta Planeada...");
                initPlannedRouteMap();
            }

            if (liveMapContainer) {
                console.log("Iniciando Mapa de Monitoreo en Vivo...");
                initLiveTrackingMap();
            }
        });
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", bootMaps);
    } else {
        // En Odoo portal los assets pueden cargarse después de DOMContentLoaded.
        bootMaps();
    }

    function waitForLeaflet(retries, intervalMs, onReady) {
        if (window.L) {
            onReady();
            return;
        }
        if (retries <= 0) {
            console.warn("Leaflet no está disponible. Verifica carga de assets frontend/CDN.");
            return;
        }
        setTimeout(function () {
            waitForLeaflet(retries - 1, intervalMs, onReady);
        }, intervalMs);
    }

    // =========================================================
    // 3. FUNCIÓN: MAPA 1 - RUTA PLANEADA
    // =========================================================
    async function initPlannedRouteMap() {
        const container = document.getElementById("route-map");
        if (!container) return;
        if (!container.dataset.rutaId) {
            console.warn("No hay ruta asignada para dibujar mapa planeado.");
            return;
        }

        const rutaId = container.dataset.rutaId;

        try {
            const response = await fetch("/custodia/ruta/" + rutaId + "/coordinates", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ params: {} })
            });

            const data = await response.json();
            const coords = data.result;

            if (!coords || coords.length < 2) {
                console.warn("La ruta no devolvió suficientes coordenadas para dibujar.", coords);
                return;
            }

            const origin = coords[0];
            const destination = coords[coords.length - 1];
            const mapRoute = L.map("route-map").setView([origin.lat, origin.lng], 6);
            L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png").addTo(mapRoute);

            let routeLayer = null;
            let distanceText = "-";
            let durationText = "-";

            try {
                const osrmUrl = `https://router.project-osrm.org/route/v1/driving/${origin.lng},${origin.lat};${destination.lng},${destination.lat}?overview=full&geometries=geojson`;
                const routeResponse = await fetch(osrmUrl);
                const routeData = await routeResponse.json();

                if (routeData.routes && routeData.routes.length > 0) {
                    const route = routeData.routes[0];
                    const routeGeo = route.geometry;
                    routeLayer = L.geoJSON(routeGeo, {
                        style: { color: "blue", weight: 5 }
                    }).addTo(mapRoute);
                    distanceText = (route.distance / 1000).toFixed(1) + " km";
                    const totalMinutes = Math.round(route.duration / 60);
                    const hours = Math.floor(totalMinutes / 60);
                    const minutes = totalMinutes % 60;
                    durationText = (hours > 0) ? `${hours} h ${minutes} min` : `${minutes} min`;
                }
            } catch (routeErr) {
                console.warn("No fue posible obtener ruta OSRM; se dibujará línea base.", routeErr);
            }

            if (!routeLayer) {
                const fallbackLine = {
                    type: "Feature",
                    geometry: {
                        type: "LineString",
                        coordinates: [
                            [origin.lng, origin.lat],
                            [destination.lng, destination.lat]
                        ]
                    }
                };
                routeLayer = L.geoJSON(fallbackLine, {
                    style: { color: "#0d6efd", weight: 4, dashArray: "8, 8" }
                }).addTo(mapRoute);
                L.marker([origin.lat, origin.lng]).addTo(mapRoute).bindPopup(origin.label || "Origen");
                L.marker([destination.lat, destination.lng]).addTo(mapRoute).bindPopup(destination.label || "Destino");
            }

            mapRoute.fitBounds(routeLayer.getBounds(), { padding: [20, 20] });

            const summaryDiv = document.getElementById("route-summary");
            if (summaryDiv) {
                const distanceEl = document.getElementById("route-distance");
                const durationEl = document.getElementById("route-duration");
                if (distanceEl) distanceEl.textContent = distanceText;
                if (durationEl) durationEl.textContent = durationText;
                summaryDiv.style.display = "block";
            }
            setTimeout(() => mapRoute.invalidateSize(), 200);
        } catch (e) {
            console.error("Error al inicializar Mapa de Ruta:", e);
        }
    }

    // =========================================================
    // 4. FUNCIÓN: MAPA 2 - MONITOREO EN VIVO
    // =========================================================
    async function initLiveTrackingMap() {
        const container = document.getElementById("live-map");
        if (!container) return;

        const serviceId = container.dataset.serviceId;
        const token = container.dataset.token;

        try {
            // Inicializamos el mapa con una vista general de México
            const mapLive = L.map("live-map").setView([23.6345, -102.5528], 5);
            L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png").addTo(mapLive);
            const marker = L.marker([23.6345, -102.5528]).addTo(mapLive);

            async function update() {
                const res = await fetch(`/mis-servicios/${serviceId}/tracking?access_token=${token}`);
                const data = await res.json();
                if (data.lat && data.lng) {
                    const pos = [data.lat, data.lng];
                    marker.setLatLng(pos).bindPopup("Última actualización: " + data.last_update).openPopup();
                    mapLive.panTo(pos);
                    // Si el zoom es el inicial muy lejano, acercamos
                    if (mapLive.getZoom() < 10) mapLive.setZoom(13);
                }
            }

            setTimeout(() => { 
                mapLive.invalidateSize(); 
                update(); 
            }, 200);

            setInterval(update, 30000);
        } catch (e) { 
            console.error("Error al inicializar Mapa en Vivo:", e); 
        }
    }
})();

# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request
import json


class CustodiaTrackingController(http.Controller):

    @http.route(
        '/api/custodia/update_location',
        type='http',
        auth='public',
        methods=['POST'],
        csrf=False
    )
    def update_location(self, **kwargs):
        """
        Endpoint para actualizar ubicación en tiempo real.
        Espera JSON:
        {
            "service_id": 1,
            "lat": 19.4326,
            "lng": -99.1332
        }
        """

        try:
            # Leer JSON del body
            data = json.loads(request.httprequest.data)

            service_id = data.get('service_id')
            lat = data.get('lat')
            lng = data.get('lng')

            # Validación básica
            if not service_id or lat is None or lng is None:
                return request.make_response(
                    json.dumps({
                        "success": False,
                        "error": "Faltan parámetros obligatorios"
                    }),
                    headers=[('Content-Type', 'application/json')]
                )

            # Buscar servicio
            service = request.env['custodia.service'].sudo().browse(int(service_id))

            if not service.exists():
                return request.make_response(
                    json.dumps({
                        "success": False,
                        "error": "Servicio no encontrado"
                    }),
                    headers=[('Content-Type', 'application/json')]
                )

            # Actualizar ubicación
            service.update_live_location(lat, lng)

            return request.make_response(
                json.dumps({
                    "success": True,
                    "message": "Ubicación actualizada correctamente"
                }),
                headers=[('Content-Type', 'application/json')]
            )

        except Exception as e:
            return request.make_response(
                json.dumps({
                    "success": False,
                    "error": str(e)
                }),
                headers=[('Content-Type', 'application/json')]
            )

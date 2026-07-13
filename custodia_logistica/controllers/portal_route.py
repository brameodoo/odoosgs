# -*- coding: utf-8 -*-

from odoo import http
from odoo.http import request


class CustodiaPortalRoute(http.Controller):

    @http.route(
        '/custodia/ruta/<int:ruta_id>/coordinates',
        type='json',
        auth='user',
        website=True
    )
    def get_route_coordinates(self, ruta_id):
        ruta = request.env['custodia.ruta'].sudo().browse(ruta_id)

        if not ruta.exists():
            return []

        return ruta.get_route_coordinates()

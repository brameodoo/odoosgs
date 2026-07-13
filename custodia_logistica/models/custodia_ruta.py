# -*- coding: utf-8 -*-

from odoo import models, fields


class CustodiaRuta(models.Model):
    _name = 'custodia.ruta'
    _description = 'Ruta Comercial de Custodia'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name'

    # =========================
    # INFORMACIÓN GENERAL
    # =========================

    name = fields.Char(
        string='Nombre de la Ruta',
        required=True,
        tracking=True,
        help="Ejemplo: GDL - Ciudad Juárez"
    )

    tipo = fields.Selection(
        [
            ('local', 'Local'),
            ('foraneo', 'Foráneo')
        ],
        string='Tipo de ruta',
        required=True,
        default='local',
        tracking=True
    )

    active = fields.Boolean(
        string='Activa',
        default=True
    )

    descripcion = fields.Text(
        string='Descripción / Detalles de la Ruta'
    )

    # =========================
    # INFORMACIÓN DEL TRAYECTO
    # =========================

    origen = fields.Char(
        string='Origen',
        tracking=True
    )

    destino = fields.Char(
        string='Destino',
        tracking=True
    )

    distancia_km = fields.Float(
        string='Distancia (km)',
        tracking=True
    )

    tiempo_estimado = fields.Float(
        string='Tiempo Estimado (horas)',
        tracking=True,
        help="Tiempo estimado en horas"
    )

    # Coordenadas Origen
    origin_latitude = fields.Float(
        string='Latitud Origen',
        digits=(10, 6)
    )

    origin_longitude = fields.Float(
        string='Longitud Origen',
        digits=(10, 6)
    )

    # Coordenadas Destino
    destination_latitude = fields.Float(
        string='Latitud Destino',
        digits=(10, 6)
    )

    destination_longitude = fields.Float(
        string='Longitud Destino',
        digits=(10, 6)
    )

    ruta_maestra_id = fields.Many2one(
        'custodia.ruta.maestra', 
        string='Ruta Maestra',
        ondelete='restrict'
    )
    clave_variante = fields.Char(string='Clave de Variante') # Ej: SOR-004/001
    
    nodo_origen_id = fields.Many2one(
        'custodia.punto.operativo', # <--- Nuevo nombre
        string='Punto de Salida'
    )
    nodo_destino_id = fields.Many2one(
        'custodia.punto.operativo', # <--- Nuevo nombre
        string='Punto de Llegada'
    )
    # =========================
    # RELACIONES
    # =========================

    node_ids = fields.One2many(
        comodel_name='custodia.ruta.nodo',
        inverse_name='ruta_id',
        string='Nodos Intermedios'
    )

    # =========================
    # COSTOS
    # =========================

    tiene_peajes = fields.Boolean(
        string='Incluye Casetas/Peajes',
        default=False
    )

    costo_peaje_estimado = fields.Monetary(
        string='Costo Estimado Peajes',
        currency_field='currency_id'
    )

    currency_id = fields.Many2one(
        'res.currency',
        string='Moneda',
        default=lambda self: self.env.company.currency_id,
        required=True
    )

    # =========================
    # MÉTODOS Y AUTOMATIZACIÓN
    # =========================

    from odoo import api # Asegúrate de que 'api' esté en los imports al inicio del archivo

    @api.onchange('ruta_maestra_id', 'nodo_origen_id', 'nodo_destino_id')
    def _onchange_compute_name(self):
        """Genera el nombre automáticamente basado en la jerarquía del Excel"""
        if self.ruta_maestra_id and self.nodo_origen_id and self.nodo_destino_id:
            self.name = f"{self.ruta_maestra_id.name} ({self.nodo_origen_id.name} > {self.nodo_destino_id.name})"

    def get_route_coordinates(self):
        """
        MODIFICADO: Extrae las coordenadas de los Puntos Operativos (Bodegas)
        en lugar de los campos de texto locales.
        """
        self.ensure_one()
        points = []

        # Origen (Desde el catálogo de Puntos Operativos)
        if self.nodo_origen_id and self.nodo_origen_id.latitude:
            points.append({
                'lat': self.nodo_origen_id.latitude,
                'lng': self.nodo_origen_id.longitude,
                'type': 'origin',
                'name': self.nodo_origen_id.name
            })

        # Destino (Desde el catálogo de Puntos Operativos)
        if self.nodo_destino_id and self.nodo_destino_id.latitude:
            points.append({
                'lat': self.nodo_destino_id.latitude,
                'lng': self.nodo_destino_id.longitude,
                'type': 'destination',
                'name': self.nodo_destino_id.name
            })

        return points

class CustodiaRutaNodo(models.Model):
    _name = 'custodia.ruta.nodo'
    _description = 'Nodo Intermedio de Ruta'
    _order = 'sequence'

    ruta_id = fields.Many2one('custodia.ruta', string='Ruta', ondelete='cascade')
    sequence = fields.Integer(string='Orden', default=10)
    name = fields.Char(string='Referencia (Punto de parada)')
    latitude = fields.Float(string='Latitud', digits=(10, 6), required=True)
    longitude = fields.Float(string='Longitud', digits=(10, 6), required=True)





# -*- coding: utf-8 -*-
from odoo import models, fields, api


class CustodiaRutaVariante(models.Model):
    _name = 'custodia.ruta.variante'
    _description = 'Variante de Ruta de Custodia'
    _order = 'name'

    name = fields.Char(
        string='Nombre de Variante',
        required=True,
        help="Ejemplo: Ruta corta autopista / Ruta alterna libre"
    )

    ruta_id = fields.Many2one(
        'custodia.ruta',
        string='Ruta Comercial',
        required=True,
        ondelete='cascade'
    )

    ubicacion_origen_id = fields.Many2one(
        'custodia.ubicacion',
        string='Ubicación Origen',
        required=True
    )

    ubicacion_destino_id = fields.Many2one(
        'custodia.ubicacion',
        string='Ubicación Destino',
        required=True
    )

    distancia_km = fields.Float(
        string='Distancia (km)',
        required=True
    )

    tiempo_estimado = fields.Float(
        string='Tiempo Estimado (Horas)',
        help="Tiempo estimado de recorrido"
    )

    activa = fields.Boolean(
        string='Activa',
        default=True
    )

    descripcion = fields.Text(
        string='Notas Logísticas'
    )

    currency_id = fields.Many2one(
        related='ruta_id.currency_id',
        store=True,
        readonly=True
    )

    costo_peaje_estimado = fields.Monetary(
        string='Costo Peaje Estimado',
        currency_field='currency_id'
    )

    @api.constrains('ubicacion_origen_id', 'ubicacion_destino_id')
    def _check_origen_destino(self):
        for record in self:
            if record.ubicacion_origen_id == record.ubicacion_destino_id:
                raise models.ValidationError(
                    "La ubicación de origen y destino no pueden ser iguales."
                )

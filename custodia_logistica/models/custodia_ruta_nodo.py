# -*- coding: utf-8 -*-

from odoo import models, fields


class CustodiaRutaNodo(models.Model):
    _name = 'custodia.ruta.nodo'
    _description = 'Nodo Intermedio de Ruta'
    _order = 'sequence, id'

    ruta_id = fields.Many2one(
        comodel_name='custodia.ruta',
        string='Ruta',
        required=True,
        ondelete='cascade',
        index=True
    )

    sequence = fields.Integer(
        string='Secuencia',
        default=10,
        help='Orden del nodo dentro de la ruta'
    )

    name = fields.Char(
        string='Nombre del Nodo',
        required=True,
        tracking=True
    )

    latitude = fields.Float(
        string='Latitud',
        digits=(10, 6),
        required=True
    )

    longitude = fields.Float(
        string='Longitud',
        digits=(10, 6),
        required=True
    )

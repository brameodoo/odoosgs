# -*- coding: utf-8 -*-
from odoo import models, fields

class CustodiaCarrier(models.Model):
    _name = 'custodia.carrier'
    _description = 'Carrier de Custodia'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Nombre del Carrier', required=True, tracking=True)
    partner_id = fields.Many2one('res.partner', string='Contacto Asociado')
    rfc = fields.Char(string='RFC')
    tipo_servicio = fields.Selection([
        ('terrestre','Terrestre'),
        ('aereo','Aéreo'),
        ('maritimo','Marítimo'),
    ], string='Tipo de Servicio', default='terrestre')
    telefono = fields.Char(string='Teléfono de Contacto')
    email = fields.Char(string='Correo Electrónico')
    notas = fields.Text(string='Notas')
    active = fields.Boolean(default=True)

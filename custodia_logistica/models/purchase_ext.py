# -*- coding: utf-8 -*-
from odoo import models, fields

class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'
    custodia_service_id = fields.Many2one('custodia.service', string='Servicio de Custodia')

# -*- coding: utf-8 -*-
from odoo import models, fields

class AccountMove(models.Model):
    _inherit = 'account.move'
    custodia_service_id = fields.Many2one('custodia.service', string='Servicio de Custodia')

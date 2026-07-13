# -*- coding: utf-8 -*-
from odoo import models, fields

class PlanningSlot(models.Model):
    _inherit = 'planning.slot'
    custodia_service_id = fields.Many2one('custodia.service', string='Servicio de Custodia')

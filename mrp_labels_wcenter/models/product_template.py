# -*- coding: utf-8 -*-
from odoo import models, fields

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    thickness = fields.Float(string="Calibre / Thickness", digits=(16, 2))
    width = fields.Float(string="Ancho / Width (Inches)", digits=(16, 2))
    material_type = fields.Char(string="Tipo de Material / Material Type", help="Ej: MP-EVOH-ALTA BARRERA")
    customer_item_code = fields.Char(string="Código de Artículo Cliente / Customer Item #")

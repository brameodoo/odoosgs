# -*- coding: utf-8 -*-
from odoo import models, fields

class MrpWorkcenter(models.Model):
    _inherit = 'mrp.workcenter'

    label_prefix = fields.Char(string="Prefijo de Etiqueta", help="Ejemplo: EE, BM, BC")
    is_final_packaging = fields.Boolean(
        string="¿Es Centro de Empaque Final?", 
        default=False,
        help="Si se marca, este centro de trabajo generará el empaque secundario (cajas) y la etiqueta Master de Tarima/Pallet."
    )

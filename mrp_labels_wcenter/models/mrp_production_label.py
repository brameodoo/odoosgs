# -*- coding: utf-8 -*-
from odoo import models, fields, api

class MrpProductionLabel(models.Model):
    _name = 'mrp.production.label'
    _description = 'Etiquetas de Producción e Insumos'
    _order = 'id desc'

    name = fields.Char(string="Lote / Identificador Etiqueta", required=True, index=True)
    label_type = fields.Selection([
        ('roll', 'Rollo / Sub-ensamble'),
        ('box', 'Caja / Empaque Secundario')
    ], string="Tipo de Etiqueta", default='roll', required=True)

    production_id = fields.Many2one('mrp.production', string="Orden de Fabricación", required=True, ondelete='cascade')
    product_id = fields.Many2one('product.product', related='production_id.product_id', string="Producto", store=True)
    workcenter_id = fields.Many2one('mrp.workcenter', string="Centro de Trabajo", required=True)
    
    weight = fields.Float(string="Peso Neto (KG)", digits=(16, 4), required=True)
    gross_weight = fields.Float(string="Peso Bruto (KG)", digits=(16, 4))
    
    operator_name = fields.Char(string="Operador")
    master_roll_ref = fields.Char(string="Rollo Maestro / Master Roll")
    box_sequence = fields.Integer(string="N° Caja")
    qty_per_box = fields.Float(string="Unidades por Caja", default=2.0)
    
    pallet_id = fields.Many2one('mrp.production.pallet', string="Tarima / Pallet", ondelete='set null')
    date_produced = fields.Datetime(string="Fecha Generada", default=fields.Datetime.now)

    def action_reprint_label(self):
        self.ensure_one()
        if self.label_type == 'roll':
            return self.env.ref('mrp_jkkpack_packaging_labels.action_report_roll_label_zpl').report_action(self)
        else:
            return self.env.ref('mrp_jkkpack_packaging_labels.action_report_box_label_zpl').report_action(self)

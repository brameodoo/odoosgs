# -*- coding: utf-8 -*-
from odoo import models, fields, api, _

class MrpProductionPallet(models.Model):
    _name = 'mrp.production.pallet'
    _description = 'Tarima / Pallet de Producción'
    _order = 'id desc'

    name = fields.Char(string="N° Tarima / Pallet ID", required=True, copy=False, readonly=True, default=lambda self: _('Nuevo'))
    production_id = fields.Many2one('mrp.production', string="Orden de Fabricación", required=True, ondelete='cascade')
    sale_order_id = fields.Many2one('sale.order', string="Pedido de Venta", related='production_id.sale_order_id', store=True)
    partner_id = fields.Many2one('res.partner', string="Cliente", related='production_id.sale_order_id.partner_id', store=True)
    customer_po = fields.Char(string="Pedido Cliente / Customer PO")
    
    label_box_ids = fields.One2many('mrp.production.label', 'pallet_id', string="Cajas en la Tarima")
    
    total_boxes = fields.Integer(string="Total Cajas/Rollos", compute='_compute_totals', store=True)
    total_qty = fields.Float(string="Cantidad por Tarima (Mill/Roll)", compute='_compute_totals', store=True)
    net_weight = fields.Float(string="Peso Neto (KG)", compute='_compute_totals', store=True, digits=(16, 2))
    gross_weight = fields.Float(string="Peso Bruto (KG)", compute='_compute_totals', store=True, digits=(16, 2))
    
    # Campo seguro para el paquete nativo sin forzar comodel estricto si no existe en la BD
    package_name = fields.Char(string="Código de Paquete Nativo", readonly=True)
    date_created = fields.Datetime(string="Fecha de Creación", default=fields.Datetime.now)

    @api.depends('label_box_ids', 'label_box_ids.weight', 'label_box_ids.gross_weight', 'label_box_ids.qty_per_box')
    def _compute_totals(self):
        for pallet in self:
            pallet.total_boxes = len(pallet.label_box_ids)
            pallet.total_qty = sum(box.qty_per_box for box in pallet.label_box_ids)
            pallet.net_weight = sum(box.weight for box in pallet.label_box_ids)
            pallet.gross_weight = sum(box.gross_weight for box in pallet.label_box_ids)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('Nuevo')) == _('Nuevo'):
                vals['name'] = self.env['ir.sequence'].next_by_code('mrp.production.pallet.sequence') or 'TR000000'
        records = super().create(vals_list)
        for record in records:
            record.package_name = record.name
            # Si el modelo de paquetes de Odoo existe en la base de datos activa, lo creamos
            if 'stock.quant.package' in self.env:
                try:
                    self.env['stock.quant.package'].create({'name': record.name})
                except Exception:
                    pass
        return records

    def action_print_pallet_master_label(self):
        self.ensure_one()
        return self.env.ref('mrp_labels_wcenter.action_report_pallet_master_zpl').report_action(self)

    def action_print_packing_list(self):
        self.ensure_one()
        return self.env.ref('mrp_labels_wcenter.action_report_packing_list_pdf').report_action(self)

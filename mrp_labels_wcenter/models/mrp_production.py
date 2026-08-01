# -*- coding: utf-8 -*-
from odoo import models, fields, api, _

class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    sale_order_name = fields.Char(string="Pedido de Venta", compute='_compute_sale_order_info', store=False)
    customer_po_no = fields.Char(string="Order Cliente PO", compute='_compute_sale_order_info', store=False)
    
    label_ids = fields.One2many('mrp.production.label', 'production_id', string="Etiquetas Emitidas")
    pallet_ids = fields.One2many('mrp.production.pallet', 'production_id', string="Tarimas / Pallets")

    @api.depends('origin')
    def _compute_sale_order_info(self):
        for mo in self:
            so_name = ''
            po_no = ''
            if mo.origin and 'sale.order' in self.env:
                so = self.env['sale.order'].search([('name', '=', mo.origin)], limit=1)
                if so:
                    so_name = so.name
                    po_no = getattr(so, 'client_order_ref', '') or ''
            else:
                so_name = mo.origin or ''

            mo.sale_order_name = so_name
            mo.customer_po_no = po_no

    def action_open_label_wizard(self):
        self.ensure_one()
        default_wc = self.workorder_ids[0].workcenter_id if self.workorder_ids else False
        is_final = default_wc.is_final_packaging if default_wc else False

        total_printed_rolls = sum(l.weight for l in self.label_ids.filtered(lambda x: x.label_type == 'roll'))
        mo_total_qty = self.product_qty
        weight_limit = max(mo_total_qty - total_printed_rolls, 0.0)

        return {
            'name': _('Generar Etiquetas y Empaque JKKPack'),
            'type': 'ir.actions.act_window',
            'res_model': 'mrp.production.label.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_production_id': self.id,
                'default_workcenter_id': default_wc.id if default_wc else False,
                'default_is_final_packaging': is_final,
                'default_mo_expected_weight': weight_limit if weight_limit > 0 else mo_total_qty,
            }
        }

    def action_open_reprint_wizard(self):
        self.ensure_one()
        return {
            'name': _('Reimpresión Selectiva de Etiquetas'),
            'type': 'ir.actions.act_window',
            'res_model': 'mrp.label.reprint.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_production_id': self.id}
        }

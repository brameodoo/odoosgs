# -*- coding: utf-8 -*-
from odoo import models, fields, api, _

class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    # Campos requeridos por vistas XML previas / personalizaciones de JKKPack
    design_no = fields.Char(string="N° de Diseño")
    
    # Campos computados guardados en BD (stored)
    sale_order_id = fields.Many2one('sale.order', string="Pedido de Venta", compute='_compute_sale_order_stored', store=True)
    customer_po_no = fields.Char(string="Order Cliente PO", compute='_compute_sale_order_stored', store=True)
    
    # Campos computados dinámicos (non-stored) para compatibilidad de vistas
    sale_reference = fields.Char(string="Referencia de Venta / Pedido", compute='_compute_sale_order_dynamic', store=False)
    customer_code = fields.Char(string="Código de Cliente", compute='_compute_sale_order_dynamic', store=False)
    customer_name = fields.Char(string="Nombre del Cliente", compute='_compute_sale_order_dynamic', store=False)
    partner_id = fields.Many2one('res.partner', string="Cliente", compute='_compute_sale_order_dynamic', store=False)
    
    # Relaciones del flujo de empaque
    label_ids = fields.One2many('mrp.production.label', 'production_id', string="Etiquetas Emitidas")
    pallet_ids = fields.One2many('mrp.production.pallet', 'production_id', string="Tarimas / Pallets")

    @api.depends('origin')
    def _compute_sale_order_stored(self):
        for mo in self:
            so = False
            if mo.origin:
                so = self.env['sale.order'].search([('name', '=', mo.origin)], limit=1)
            mo.sale_order_id = so.id if so else False
            mo.customer_po_no = so.client_order_ref if so else ''

    @api.depends('sale_order_id', 'origin')
    def _compute_sale_order_dynamic(self):
        for mo in self:
            so = mo.sale_order_id
            mo.sale_reference = so.name if so else (mo.origin or '')
            mo.partner_id = so.partner_id.id if (so and so.partner_id) else False
            mo.customer_code = so.partner_id.ref if (so and so.partner_id) else ''
            mo.customer_name = so.partner_id.name if (so and so.partner_id) else ''

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

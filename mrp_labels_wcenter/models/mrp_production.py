# -*- coding: utf-8 -*-
from odoo import models, fields, api, _

class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    # --- FIX OWL ERROR: Campo solicitado por la vista XML ---
    bom_reference = fields.Char(
        string="Referencia BoM", 
        related='bom_id.code', 
        store=True, 
        readonly=True
    )

    design_no = fields.Char(string="N° de Diseño")
    
    sale_order_id = fields.Many2one(
        'sale.order', 
        string="Pedido de Venta", 
        compute='_compute_sale_order_stored', 
        store=True, 
        readonly=False
    )
    customer_po_no = fields.Char(
        string="Order Cliente PO", 
        compute='_compute_sale_order_stored', 
        store=True, 
        readonly=False
    )
    
    # Campos dinámicos para interfaz
    sale_reference = fields.Char(string="Referencia de Venta / Pedido", compute='_compute_sale_order_dynamic')
    customer_code = fields.Char(string="Código de Cliente", compute='_compute_sale_order_dynamic')
    customer_name = fields.Char(string="Nombre del Cliente", compute='_compute_sale_order_dynamic')
    partner_id = fields.Many2one('res.partner', string="Cliente", compute='_compute_sale_order_dynamic', store=False)
    
    label_ids = fields.One2many('mrp.production.label', 'production_id', string="Etiquetas Emitidas")
    pallet_ids = fields.One2many('mrp.production.pallet', 'production_id', string="Tarimas / Pallets")

    @api.depends('origin')
    def _compute_sale_order_stored(self):
        for mo in self:
            so = False
            if mo.origin:
                so = self.env['sale.order'].search([('name', '=', mo.origin)], limit=1)
            mo.sale_order_id = so if so else False
            mo.customer_po_no = so.client_order_ref if so and so.client_order_ref else ''

    @api.depends('sale_order_id', 'sale_order_id.partner_id')
    def _compute_sale_order_dynamic(self):
        for mo in self:
            so = mo.sale_order_id
            mo.sale_reference = so.name if so else (mo.origin or '')
            # Asignación correcta de recordset en lugar de .id
            mo.partner_id = so.partner_id if so else False
            mo.customer_code = so.partner_id.ref if so and so.partner_id else ''
            mo.customer_name = so.partner_id.name if so and so.partner_id else ''

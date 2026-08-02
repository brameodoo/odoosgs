# -*- coding: utf-8 -*-
from odoo import models, fields, api, _

class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    # --- FIX CRÍTICO OWL: Campos requeridos por vistas XML antiguas/heredadas ---
    bom_reference = fields.Char(
        string="Referencia BoM", 
        related='bom_id.code', 
        store=True, 
        readonly=True
    )

    production_type = fields.Selection([
        ('standard', 'Estándar'),
        ('custom', 'Especial / Personalizada'),
    ], string="Tipo de Producción", default='standard')

    # FIX: Se agregan estos campos para resolver las vistas de 'jkk_report' / vistas heredadas
    origin_type = fields.Selection([
        ('so', 'Pedido de Venta'),
        ('mrp', 'Orden de Fabricación Padre'),
        ('manual', 'Manual / Stock'),
    ], string="Tipo de Origen", compute='_compute_origin_type', store=True)

    order_type = fields.Selection([
        ('normal', 'Normal'),
        ('rework', 'Reproceso'),
        ('sample', 'Muestra'),
    ], string="Tipo de Orden", default='normal')

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
    
    # Campos dinámicos para interfaz de etiquetas / consultas
    sale_reference = fields.Char(
        string="Referencia de Venta / Pedido", 
        compute='_compute_sale_order_dynamic'
    )
    customer_code = fields.Char(
        string="Código de Cliente", 
        compute='_compute_sale_order_dynamic'
    )
    customer_name = fields.Char(
        string="Nombre del Cliente", 
        compute='_compute_sale_order_dynamic'
    )
    partner_id = fields.Many2one(
        'res.partner', 
        string="Cliente", 
        compute='_compute_sale_order_dynamic', 
        store=False
    )
    
    # Relaciones One2many
    label_ids = fields.One2many(
        'mrp.production.label', 
        'production_id', 
        string="Etiquetas Emitidas"
    )
    pallet_ids = fields.One2many(
        'mrp.production.pallet', 
        'production_id', 
        string="Tarimas / Pallets"
    )

    @api.depends('origin', 'procurement_group_id')
    def _compute_origin_type(self):
        for mo in self:
            if mo.origin and mo.origin.startswith('SO'):
                mo.origin_type = 'so'
            elif mo.origin and mo.origin.startswith('MO'):
                mo.origin_type = 'mrp'
            else:
                mo.origin_type = 'manual'

    @api.depends('origin', 'procurement_group_id')
    def _compute_sale_order_stored(self):
        for mo in self:
            so = False
            # 1. Intentar obtener el Pedido de Venta por el Grupo de Abastecimiento (Optimizado / Nativo Odoo)
            if mo.procurement_group_id and mo.procurement_group_id.mrp_production_ids:
                so = mo.procurement_group_id.sale_id
            
            # 2. Búsqueda por coincidencia de origen si no se encontró por grupo
            if not so and mo.origin:
                so = self.env['sale.order'].search([('name', '=', mo.origin)], limit=1)
                
            mo.sale_order_id = so if so else False
            mo.customer_po_no = so.client_order_ref if so and so.client_order_ref else ''

    @api.depends('sale_order_id', 'sale_order_id.partner_id')
    def _compute_sale_order_dynamic(self):
        for mo in self:
            so = mo.sale_order_id
            mo.sale_reference = so.name if so else (mo.origin or '')
            mo.partner_id = so.partner_id if so else False
            mo.customer_code = so.partner_id.ref if so and so.partner_id else ''
            mo.customer_name = so.partner_id.name if so and so.partner_id else ''

    # --- ACCIONES PARA BOTONES EN VISTAS XML ---

    def action_open_label_wizard(self):
        """Abre el asistente para la generación / impresión de etiquetas."""
        self.ensure_one()
        return {
            'name': _('Generar Etiquetas'),
            'type': 'ir.actions.act_window',
            'res_model': 'mrp.production.label.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_production_id': self.id,
                'default_product_id': self.product_id.id,
            }
        }

    def action_open_reprint_wizard(self):
        """Abre el asistente para la reimpresión de etiquetas."""
        self.ensure_one()
        return {
            'name': _('Reimprimir Etiquetas'),
            'type': 'ir.actions.act_window',
            'res_model': 'mrp.production.label.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_production_id': self.id,
                'default_reprint_mode': True,
            }
        }

    def action_open_pallet_wizard(self):
        """Abre el asistente para la gestión / armado de tarimas."""
        self.ensure_one()
        # Verificación segura para evitar crash si el modelo/wizard no existe
        if 'mrp.production.pallet.wizard' in self.env:
            return {
                'name': _('Generar Tarima / Pallet'),
                'type': 'ir.actions.act_window',
                'res_model': 'mrp.production.pallet.wizard',
                'view_mode': 'form',
                'target': 'new',
                'context': {
                    'default_production_id': self.id,
                    'default_product_id': self.product_id.id,
                }
            }
        return True

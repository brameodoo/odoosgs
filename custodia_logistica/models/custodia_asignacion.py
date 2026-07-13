# -*- coding: utf-8 -*-
from odoo import models, fields

class CustodiaAsignacion(models.Model):
    _name = 'custodia.asignacion'
    _description = 'Asignación de Custodia'

    service_id = fields.Many2one('custodia.service', string='Servicio', required=True, ondelete='cascade')
    notes = fields.Text(string='Notas de asignación')

    employee_ids = fields.Many2many('hr.employee',
                                    'custodia_asignacion_employee_rel',
                                    'asignacion_id', 'employee_id',
                                    string='Personal asignado')

    vehicle_ids = fields.Many2many('fleet.vehicle',
                                   'custodia_asignacion_vehicle_rel',
                                   'asignacion_id', 'vehicle_id',
                                   string='Vehículos')

    candado_ids = fields.Many2many('product.product',
                                   'custodia_asignacion_candado_rel',
                                   'asignacion_id', 'product_id',
                                   string='Candados',
                                   domain=[('type', '=', 'product')])

    radio_ids = fields.Many2many('product.product',
                                 'custodia_asignacion_radio_rel',
                                 'asignacion_id', 'product_id',
                                 string='Radios',
                                 domain=[('type', '=', 'product')])

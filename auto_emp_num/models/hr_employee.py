from odoo import models, fields, api, _
from odoo.exceptions import UserError
from datetime import datetime

class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    registration_number = fields.Char(string="ID Empleado", copy=False, tracking=True)
    # Definimos el campo para que Odoo lo reconozca
    contract_date_start = fields.Date(string="Fecha de Contrato (Importada)")

    def action_generate_numbers_by_seniority(self):
        employees = self.search([])
        
        if not employees:
            raise UserError("No hay empleados en el sistema.")

        # 1. Reiniciar secuencia a 1
        sequence = self.env['ir.sequence'].search([('code', '=', 'hr.employee.number')], limit=1)
        if sequence:
            sequence.write({'number_next_actual': 1})

        # 2. Función de ordenamiento segura
        def get_cleaning_date(emp):
            # Si tiene la fecha importada del Excel, esa manda
            if emp.contract_date_start:
                return emp.contract_date_start
            
            # Si no hay fecha importada, usamos la fecha de creación.
            # Convertimos Datetime a Date de forma nativa en Python (.date())
            if emp.create_date:
                return emp.create_date.date()
            
            # Si de plano no hay nada (muy raro), devolvemos la fecha de hoy
            return fields.Date.today()

        # 3. Ordenar y asignar
        sorted_employees = sorted(employees, key=get_cleaning_date)

        for emp in sorted_employees:
            new_seq = self.env['ir.sequence'].next_by_code('hr.employee.number')
            numeric_pin = ''.join(filter(str.isdigit, new_seq))
            
            emp.write({
                'registration_number': new_seq,
                'pin': numeric_pin
            })
        
        return {
            'effect': {
                'fadeout': 'slow',
                'message': '¡Numeración corregida con éxito!',
                'type': 'rainbow_man',
            }
        }

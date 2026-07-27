# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class MrpProductionLabelWizard(models.TransientModel):
    _name = 'mrp.production.label.wizard'
    _description = 'Asistente de Pesaje, Etiquetado y Empaque'

    production_id = fields.Many2one('mrp.production', string="Orden de Fabricación", required=True)
    workcenter_id = fields.Many2one('mrp.workcenter', string="Centro de Trabajo Originario", required=True)
    is_final_packaging = fields.Boolean(string="¿Es Empaque Final?", readonly=True)
    
    qty_labels = fields.Integer(string="Número de Unidades (Rollos/Cajas)", default=1, required=True)
    mo_expected_weight = fields.Float(string="Límite por Producir (KG)", digits=(16, 4), readonly=True)
    
    # Campos específicos para Empaque Final (Cajas / Pallet)
    operator_name = fields.Char(string="Nombre del Operador")
    master_roll_prefix = fields.Char(string="Prefijo Rollo Maestro", default="BMC")
    rolls_per_box = fields.Float(string="Rollos/Unidades por Caja", default=2.0)
    box_tare_weight = fields.Float(string="Tara Por Caja (KG)", default=0.84)
    
    line_ids = fields.One2many('mrp.production.label.wizard.line', 'wizard_id', string="Captura de Pesos")

    @api.onchange('workcenter_id')
    def _onchange_workcenter_id(self):
        if self.workcenter_id:
            self.is_final_packaging = self.workcenter_id.is_final_packaging

    @api.onchange('qty_labels')
    def _onchange_qty_labels(self):
        commands = [(5, 0, 0)]
        for i in range(self.qty_labels):
            commands.append((0, 0, {
                'sequence_no': i + 1,
                'weight': 0.0,
                'gross_weight': 0.0
            }))
        self.line_ids = commands

    def generate_and_print_labels(self):
        self.ensure_one()
        total_wizard_weight = sum(line.weight for line in self.line_ids)
        
        if total_wizard_weight <= 0:
            raise ValidationError(_("El peso total ingresado debe ser mayor a cero."))
            
        if not self.is_final_packaging and total_wizard_weight > (self.mo_expected_weight + 0.001):
            raise ValidationError(_(
                "El peso total de los rollos (%(total)s kg) excede el saldo pendiente (%(limit)s kg).",
                total=total_wizard_weight, limit=self.mo_expected_weight
            ))

        created_labels = self.env['mrp.production.label']
        prefix = self.workcenter_id.label_prefix or self.workcenter_id.code or 'GEN'

        if not self.is_final_packaging:
            # GENERACIÓN DE ETIQUETAS POR ROLLO (PROCESO INTERMEDIO)
            for line in self.line_ids:
                if line.weight <= 0:
                    raise ValidationError(_("Cada rollo debe tener un peso válido."))
                
                seq_num = self.env['ir.sequence'].next_by_code('mrp.production.roll.label.sequence')
                label_name = f"{prefix}{seq_num}"

                label = self.env['mrp.production.label'].create({
                    'name': label_name,
                    'label_type': 'roll',
                    'production_id': self.production_id.id,
                    'workcenter_id': self.workcenter_id.id,
                    'weight': line.weight,
                })
                created_labels |= label

            return self.env.ref('mrp_jkkpack_packaging_labels.action_report_roll_label_zpl').report_action(created_labels)

        else:
            # GENERACIÓN DE EMPAQUE FINAL (CAJAS Y PALLET MASTER)
            pallet = self.env['mrp.production.pallet'].create({
                'production_id': self.production_id.id,
                'customer_po': self.production_id.customer_po_no,
            })

            for line in self.line_ids:
                if line.weight <= 0:
                    raise ValidationError(_("Cada caja debe tener un peso neto válido."))
                
                box_code = f"{pallet.name}-{line.sequence_no}"
                m_roll_seq = self.env['ir.sequence'].next_by_code('mrp.production.roll.label.sequence')
                master_roll = f"{self.master_roll_prefix}{m_roll_seq}"

                gross_w = line.gross_weight if line.gross_weight > 0 else (line.weight + self.box_tare_weight)

                label = self.env['mrp.production.label'].create({
                    'name': box_code,
                    'label_type': 'box',
                    'production_id': self.production_id.id,
                    'workcenter_id': self.workcenter_id.id,
                    'weight': line.weight,
                    'gross_weight': gross_w,
                    'operator_name': self.operator_name,
                    'master_roll_ref': master_roll,
                    'box_sequence': line.sequence_no,
                    'qty_per_box': self.rolls_per_box,
                    'pallet_id': pallet.id,
                })
                created_labels |= label

            # Retornar la impresión master de la Tarima
            return pallet.action_print_pallet_master_label()


class MrpProductionLabelWizardLine(models.TransientModel):
    _name = 'mrp.production.label.wizard.line'
    _description = 'Línea de captura individual de Peso'

    wizard_id = fields.Many2one('mrp.production.label.wizard', ondelete='cascade')
    sequence_no = fields.Integer(string="N° Elemento", readonly=True)
    weight = fields.Float(string="Peso Neto (KG)", digits=(16, 4), required=True)
    gross_weight = fields.Float(string="Peso Bruto (KG)", digits=(16, 4))

# -*- coding: utf-8 -*-
from odoo import models, fields, _
from odoo.exceptions import UserError

class MrpLabelReprintWizard(models.TransientModel):
    _name = 'mrp.label.reprint.wizard'
    _description = 'Asistente para Reimpresión Parcial o Total'

    production_id = fields.Many2one('mrp.production', string="Orden de Fabricación", required=True)
    reprint_option = fields.Selection([
        ('all', 'Imprimir Tira Completa'),
        ('select', 'Selección Individual de Etiquetas')
    ], string="Modo de Reimpresión", default='all', required=True)
    
    label_ids = fields.Many2many('mrp.production.label', string="Etiquetas a Reimprimir")

    def action_reprint(self):
        self.ensure_one()
        labels_to_print = self.env['mrp.production.label']
        
        if self.reprint_option == 'all':
            labels_to_print = self.production_id.label_ids
        else:
            labels_to_print = self.label_ids

        if not labels_to_print:
            raise UserError(_("No hay etiquetas seleccionadas para reimprimir."))

        roll_labels = labels_to_print.filtered(lambda x: x.label_type == 'roll')
        box_labels = labels_to_print.filtered(lambda x: x.label_type == 'box')

        if roll_labels and not box_labels:
            return self.env.ref('mrp_jkkpack_packaging_labels.action_report_roll_label_zpl').report_action(roll_labels)
        elif box_labels and not roll_labels:
            return self.env.ref('mrp_jkkpack_packaging_labels.action_report_box_label_zpl').report_action(box_labels)
        else:
            return self.env.ref('mrp_jkkpack_packaging_labels.action_report_roll_label_zpl').report_action(labels_to_print)


import base64
import io
import unicodedata
import re
from difflib import SequenceMatcher
import openpyxl

from odoo import api, fields, models, _
from odoo.exceptions import UserError

def normalize_name(name):
    if not name:
        return ""
    name = str(name).replace('\xa0', ' ').replace('\u200b', ' ').replace('\t', ' ')
    name = ''.join(c for c in unicodedata.normalize('NFD', name) if unicodedata.category(c) != 'Mn')
    name = name.upper()
    name = re.sub(r'[^A-Z0-9\s]', ' ', name)
    name = re.sub(r'\s+', ' ', name).strip()
    return name

def token_sort_ratio(a, b):
    a_tokens = sorted(normalize_name(a).split())
    b_tokens = sorted(normalize_name(b).split())
    return SequenceMatcher(None, ' '.join(a_tokens), ' '.join(b_tokens)).ratio()

class SgsPerdiemDepositImportWizard(models.TransientModel):
    _name = 'sgs.perdiem.deposit.import.wizard'
    _description = 'Importador inteligente de depositos'

    file = fields.Binary('Archivo Excel', required=True)
    filename = fields.Char('Nombre archivo')
    date_default = fields.Date('Fecha por defecto', default=fields.Date.context_today)
    line_ids = fields.One2many('sgs.perdiem.deposit.import.line', 'wizard_id', string='Lineas a conciliar')
    state = fields.Selection([('draft','Carga'),('to_conciliate','Conciliar'),('done','Hecho')], default='draft')

    def action_parse_file(self):
        self.ensure_one()
        data = base64.b64decode(self.file)
        try:
            wb = openpyxl.load_workbook(io.BytesIO(data), data_only=True)
        except Exception as e:
            raise UserError(f"No se pudo leer el Excel: {e}")
        ws = wb['Sheet1'] if 'Sheet1' in wb.sheetnames else wb.active
        
        custodians = self.env['sgs.custodian'].search([])
        employees = self.env['hr.employee'].search([])
        cust_map = {normalize_name(c.name): c for c in custodians}
        emp_map = {normalize_name(e.name): e for e in employees}

        lines = []
        for row in ws.iter_rows(min_row=2, values_only=True):
            if not any(row):
                continue
            raw_name = str(row[1] or '').strip()
            if not raw_name or 'CUSTODIO' in normalize_name(raw_name):
                continue
            amount = row[5] or 0
            date_val = row[0] or self.date_default
            concept = str(row[4] or 'Deposito semanal viaticos').strip()

            norm = normalize_name(raw_name)
            custodian = cust_map.get(norm)
            employee = emp_map.get(norm)
            status = 'matched'
            score = 1.0

            if not custodian and employee:
                custodian = self.env['sgs.custodian'].search([('employee_id','=',employee.id)], limit=1)
            
            if not custodian:
                best_match = None
                best_score = 0
                for c_name, c_rec in cust_map.items():
                    if not set(norm.split()) & set(c_name.split()):
                        continue
                    s = token_sort_ratio(norm, c_name)
                    if s > best_score:
                        best_score = s
                        best_match = c_rec
                if best_score >= 0.88:
                    custodian = best_match
                    score = best_score
                    status = 'matched_auto'
                elif best_score >= 0.60:
                    custodian = best_match
                    score = best_score
                    status = 'to_conciliate'
                else:
                    status = 'not_found'
                    score = best_score

            lines.append((0,0,{
                'custodio_raw': raw_name,
                'custodio_normalized': norm,
                'custodian_id': custodian.id if custodian else False,
                'employee_id': employee.id if employee else (custodian.employee_id.id if custodian and custodian.employee_id else False),
                'date': date_val,
                'amount': float(amount) if amount else 0.0,
                'concept': concept,
                'match_score': score,
                'state': status,
                'to_import': bool(custodian and float(amount or 0) > 0),
            }))
        
        self.line_ids = [(5,0,0)] + lines
        self.state = 'to_conciliate'
        return {
            'type':'ir.actions.act_window',
            'res_model': self._name,
            'res_id': self.id,
            'view_mode':'form',
            'target':'new',
        }

    def action_create_deposits(self):
        to_create = self.line_ids.filtered(lambda l: l.state in ('matched','matched_auto','to_conciliate') and l.custodian_id and l.to_import)
        if not to_create:
            raise UserError("No hay lineas validas. Asigna custodios manualmente o marca Importar.")
        vals_list = []
        for line in to_create:
            if line.amount <= 0:
                continue
            vals_list.append({
                'custodian_id': line.custodian_id.id,
                'date': line.date,
                'amount': line.amount,
                'concept': line.concept,
            })
        deposits = self.env['sgs.perdiem.deposit'].create(vals_list)
        self.state = 'done'
        return {
            'type':'ir.actions.act_window',
            'name':'Depositos creados',
            'res_model':'sgs.perdiem.deposit',
            'domain':[('id','in',deposits.ids)],
            'view_mode':'list,form',
        }

class SgsPerdiemDepositImportLine(models.TransientModel):
    _name = 'sgs.perdiem.deposit.import.line'
    _description = 'Linea de conciliacion de deposito'

    wizard_id = fields.Many2one('sgs.perdiem.deposit.import.wizard', required=True, ondelete='cascade')
    custodio_raw = fields.Char('Nombre en Excel', readonly=True)
    custodio_normalized = fields.Char('Normalizado', readonly=True)
    employee_id = fields.Many2one('hr.employee', string='Empleado encontrado')
    custodian_id = fields.Many2one('sgs.custodian', string='Custodio a depositar')
    date = fields.Date('Fecha')
    amount = fields.Float('Monto')
    concept = fields.Char('Concepto')
    match_score = fields.Float('Score', digits=(3,2))
    state = fields.Selection([
        ('matched','Coincidencia exacta'),
        ('matched_auto','Auto-conciliado'),
        ('to_conciliate','Requiere revision'),
        ('not_found','No encontrado')
    ], default='to_conciliate')
    to_import = fields.Boolean('Importar', default=True)

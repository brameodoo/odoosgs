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
    # 1. Reemplaza caracteres invisibles que trae tu excel
    name = str(name).replace('\xa0', ' ').replace('\u200b', ' ').replace('\t', ' ')
    # 2. Quita acentos
    name = ''.join(c for c in unicodedata.normalize('NFD', name) if unicodedata.category(c) != 'Mn')
    # 3. Upper + solo letras y numeros
    name = name.upper()
    name = re.sub(r'[^A-Z0-9\s]', ' ', name) # quita comas, puntos
    name = re.sub(r'\s+', ' ', name).strip()
    return name

def token_sort_ratio(a, b):
    # Para manejar APELLIDO NOMBRE vs NOMBRE APELLIDO
    a_tokens = sorted(normalize_name(a).split())
    b_tokens = sorted(normalize_name(b).split())
    return SequenceMatcher(None, ' '.join(a_tokens), ' '.join(b_tokens)).ratio()

class SgsPerdiemDepositImportWizard(models.TransientModel):
    _name = 'sgs.perdiem.deposit.import.wizard'
    _description = 'Importador inteligente de depósitos'

    file = fields.Binary('Archivo Excel', required=True)
    filename = fields.Char('Nombre archivo')
    date_default = fields.Date('Fecha por defecto', default=fields.Date.context_today)
    
    line_ids = fields.One2many('sgs.perdiem.deposit.import.line', 'wizard_id', string='Líneas a conciliar')
    state = fields.Selection([('draft','Carga'),('to_conciliate','Conciliar'),('done','Hecho')], default='draft')

    def action_parse_file(self):
        self.ensure_one()
        if not self.file:
            raise UserError("Sube un archivo")
        
        data = base64.b64decode(self.file)
        wb = openpyxl.load_workbook(io.BytesIO(data), data_only=True)
        ws = wb['Sheet1'] if 'Sheet1' in wb.sheetnames else wb.active
        
        # Lee encabezados
        headers = [normalize_name(c.value) for c in next(ws.iter_rows(min_row=1, max_row=1))]
        # Mapeo flexible
        col_map = {}
        for idx, h in enumerate(headers):
            if 'FECHA' in h and 'DEPOSITO' in h: col_map['date'] = idx
            if 'CUSTODIO' in h: col_map['custodio_raw'] = idx
            if 'MONTO' in h: col_map['amount'] = idx
            if 'CONCEPTO' in h: col_map['concept'] = idx

        # Cache de custodios y empleados normalizados
        custodians = self.env['sgs.custodian'].search([])
        employees = self.env['hr.employee'].search([])
        
        cust_map = {normalize_name(c.name): c for c in custodians}
        emp_map = {normalize_name(e.name): e for e in employees}
        # Tambien mapa por token sort para busqueda rapida
        all_cust_names = list(cust_map.keys())

        lines = []
        for row in ws.iter_rows(min_row=2, values_only=True):
            if not any(row): continue
            raw_name = str(row[col_map.get('custodio_raw',1)] or '').strip()
            if not raw_name: continue
            
            norm = normalize_name(raw_name)
            amount = row[col_map.get('amount',5)] or 0
            date = row[col_map.get('date',0)] or self.date_default
            concept = row[col_map.get('concept',4)] or 'Depósito semanal viáticos'

            custodian = cust_map.get(norm)
            employee = emp_map.get(norm)
            status = 'matched'
            score = 1.0

            # 1. Intento exacto normalizado
            if not custodian and employee:
                custodian = self.env['sgs.custodian'].search([('employee_id','=',employee.id)], limit=1)
            
            # 2. Intento fuzzy token_sort si no hay exacto
            if not custodian:
                best_match = None
                best_score = 0
                for c_name, c_rec in cust_map.items():
                    s = token_sort_ratio(norm, c_name)
                    if s > best_score:
                        best_score = s
                        best_match = c_rec
                if best_score >= 0.85:
                    custodian = best_match
                    score = best_score
                    status = 'matched_auto'
                elif best_score >= 0.65:
                    custodian = best_match
                    score = best_score
                    status = 'to_conciliate'
                else:
                    status = 'not_found'

            lines.append((0,0,{
                'custodio_raw': raw_name,
                'custodio_normalized': norm,
                'custodian_id': custodian.id if custodian else False,
                'employee_id': employee.id if employee else (custodian.employee_id.id if custodian else False),
                'date': date,
                'amount': float(amount),
                'concept': concept,
                'match_score': score,
                'state': status,
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
        # Solo crea los que estan validados
        to_create = self.line_ids.filtered(lambda l: l.state in ('matched','matched_auto') and l.custodian_id and l.to_import)
        vals_list = []
        for line in to_create:
            if line.amount <= 0: continue
            vals_list.append({
                'custodian_id': line.custodian_id.id,
                'date': line.date,
                'amount': line.amount,
                'concept': line.concept,
            })
        if not vals_list:
            raise UserError("No hay líneas válidas para importar. Concilia manualmente las que están en amarillo/rojo.")
        
        self.env['sgs.perdiem.deposit'].create(vals_list)
        self.state = 'done'
        return {
            'type':'ir.actions.client',
            'tag':'display_notification',
            'params':{'title': f'Se crearon {len(vals_list)} depósitos correctamente', 'type':'success'}
        }

class SgsPerdiemDepositImportLine(models.TransientModel):
    _name = 'sgs.perdiem.deposit.import.line'
    _description = 'Línea de conciliación de depósito'

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
        ('matched_auto','Auto-conciliado (fuzzy)'),
        ('to_conciliate','Requiere revisión'),
        ('not_found','No encontrado')
    ], default='to_conciliate')
    
    to_import = fields.Boolean('Importar', default=True, help="Desmarca si es un empleado que no quieres abonar / no dado de alta")

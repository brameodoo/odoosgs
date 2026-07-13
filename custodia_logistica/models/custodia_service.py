# -*- coding: utf-8 -*-
from datetime import timedelta

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class CustodiaService(models.Model):
    _name = 'custodia.service'
    _description = 'Servicio de Custodia'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'portal.mixin']
    _order = 'sequence desc, start_datetime desc, id desc'

    name = fields.Char(string='Folio del Servicio', required=True, copy=False, default='Nuevo', tracking=True)

    sequence = fields.Char(string='Consecutivo', copy=False, readonly=True, default='Nuevo', index=True)

    partner_id = fields.Many2one('res.partner', string='Cliente', required=True, tracking=True)
    contact_id = fields.Many2one('res.partner', string='Persona solicitante', required=True, tracking=True)

    planner_id = fields.Many2one('res.users', string='Planeador', tracking=True)

    carrier_id = fields.Many2one('custodia.carrier', string='Carrier', tracking=True)
    ruta_id = fields.Many2one('custodia.ruta', string='Ruta', tracking=True)

    # Compatibilidad con vistas/catálogos existentes
    ruta_maestra_id = fields.Many2one('custodia.ruta.maestra', string='Ruta Principal', tracking=True)
    nodo_origen_id = fields.Many2one('custodia.punto.operativo', string='Punto de Salida', tracking=True)
    nodo_destino_id = fields.Many2one('custodia.punto.operativo', string='Punto de Llegada', tracking=True)
    ruta_tipo = fields.Selection(related='ruta_id.tipo', string='Tipo de ruta', store=True, readonly=True)

    start_datetime = fields.Datetime(string='Fecha programada', required=True, tracking=True)
    nivel_seguridad = fields.Selection(
        [
            ('1', 'Nivel 1'),
            ('2', 'Nivel 2'),
            ('3', 'Nivel 3'),
            ('4', 'Nivel 4'),
            ('4x', 'Excepción + Nivel 4'),
        ],
        string='Nivel de seguridad',
        tracking=True,
    )

    load_id = fields.Char(string='Load ID', index=True, tracking=True)

    # Ubicación y eventos de ejecución
    current_lat = fields.Float(string='Latitud Actual', tracking=True)
    current_lng = fields.Float(string='Longitud Actual', tracking=True)
    last_update = fields.Datetime(string='Última Actualización', tracking=True)
    gps_tracking_url = fields.Char(string='Liga GPS en tiempo real', tracking=True)

    hora_llegada = fields.Datetime(string='Hora de llegada custodio', tracking=True)
    hora_inicio_real = fields.Datetime(string='Hora de inicio real', tracking=True)

    diff_llegada_min = fields.Integer(string='Diferencia llegada (min)', compute='_compute_diferencias')
    diff_inicio_min = fields.Integer(string='Diferencia inicio (min)', compute='_compute_diferencias')

    tipo_unidad = fields.Char(string='Tipo de unidad', tracking=True)
    placas = fields.Char(string='Placas', tracking=True)
    transporte = fields.Char(string='Transporte', tracking=True)
    operador1_nombre = fields.Char(string='Operador 1', tracking=True)
    tel_monitoreo_1 = fields.Char(string='Teléfono Monitoreo 1', tracking=True)
    tel_monitoreo_2 = fields.Char(string='Teléfono Monitoreo 2', tracking=True)
    operador2_nombre = fields.Char(string='Operador 2', tracking=True)
    operador1_licencia = fields.Char(string='Licencia Operador 1', tracking=True)
    operador2_licencia = fields.Char(string='Licencia Operador 2', tracking=True)
    start_coords = fields.Char(string='Coordenadas de inicio', tracking=True)
    end_coords = fields.Char(string='Coordenadas de llegada', tracking=True)
    comentarios_cliente = fields.Text(string='Comentarios del Cliente', tracking=True)

    asignacion_ids = fields.One2many('custodia.asignacion', 'service_id', string='Asignaciones')
    tracking_ids = fields.One2many('custodia.service.tracking', 'service_id', string='Historial de Ubicaciones')

    request_type = fields.Selection(
        [('alerta', 'Alerta'), ('servicio', 'Servicio')],
        string='Tipo de registro',
        required=True,
        default='alerta',
        tracking=True,
        index=True,
    )

    state = fields.Selection(
        [
            ('alerta', 'Alerta'),
            ('solicitado', 'Solicitado'),
            ('aprobado', 'Aprobado'),
            ('asignado', 'Asignado'),
            ('en_ejecucion', 'En ejecución'),
            ('finalizado', 'Finalizado'),
            ('cancelado', 'Cancelado'),
        ],
        string='Estado',
        default='alerta',
        tracking=True,
        index=True,
    )

    calendar_color = fields.Integer(string='Color calendario', compute='_compute_calendar_color', store=False)

    @api.depends('request_type', 'state')
    def _compute_calendar_color(self):
        color_map = {
            'alerta': 2,
            'solicitado': 3,
            'aprobado': 3,
            'asignado': 3,
            'en_ejecucion': 10,
            'finalizado': 7,
            'cancelado': 8,
        }
        for rec in self:
            if rec.request_type == 'alerta' or rec.state == 'alerta':
                rec.calendar_color = color_map['alerta']
            else:
                rec.calendar_color = color_map.get(rec.state, 1)

    @api.depends('start_datetime', 'hora_llegada', 'hora_inicio_real')
    def _compute_diferencias(self):
        for record in self:
            diff_llegada = 0
            diff_inicio = 0
            if record.start_datetime:
                if record.hora_llegada:
                    diff = (record.hora_llegada - record.start_datetime).total_seconds() / 60
                    diff_llegada = int(diff)
                if record.hora_inicio_real:
                    diff = (record.hora_inicio_real - record.start_datetime).total_seconds() / 60
                    diff_inicio = int(diff)
            record.diff_llegada_min = diff_llegada
            record.diff_inicio_min = diff_inicio

    @api.constrains('request_type', 'start_datetime')
    def _check_alerta_lead_time(self):
        now = fields.Datetime.now()
        for rec in self:
            if rec.request_type == 'alerta' and rec.start_datetime:
                if rec.start_datetime <= now + timedelta(hours=24):
                    raise ValidationError(_(
                        'La alerta debe programarse con al menos 24 horas de anticipación. '
                        'Para servicios urgentes, capture directamente el servicio completo.'
                    ))

    def _get_missing_service_fields(self):
        self.ensure_one()
        missing = []
        checks = [
            (_('Contacto solicitante'), self.contact_id),
            (_('Fecha programada'), self.start_datetime),
            (_('Carrier'), self.carrier_id),
            (_('Ruta'), self.ruta_id),
            (_('Nivel de seguridad'), self.nivel_seguridad),
            (_('Load ID'), self.load_id),
        ]
        for label, value in checks:
            if not value:
                missing.append(label)
        return missing

    def _raise_if_missing_service_fields(self):
        for rec in self:
            missing = rec._get_missing_service_fields()
            if missing:
                raise ValidationError(_('Para convertir a servicio faltan campos: %s') % ', '.join(missing))

    @api.constrains('request_type', 'carrier_id', 'ruta_id', 'nivel_seguridad', 'load_id', 'contact_id', 'start_datetime')
    def _check_required_for_service(self):
        for rec in self:
            if rec.request_type == 'servicio':
                rec._raise_if_missing_service_fields()

    @api.constrains('load_id')
    def _check_unique_load_id(self):
        for rec in self:
            if not rec.load_id:
                continue
            dup = self.search([
                ('id', '!=', rec.id),
                ('load_id', '=', rec.load_id),
            ], limit=1)
            if dup:
                raise ValidationError(_(
                    "El Load ID '%(load)s' ya está registrado en %(folio)s (estado: %(state)s, fecha: %(date)s)."
                ) % {
                    'load': rec.load_id,
                    'folio': dup.name,
                    'state': dup.state,
                    'date': fields.Datetime.to_string(dup.start_datetime) if dup.start_datetime else '-',
                })

    @api.model_create_multi
    def create(self, vals_list):
        seq = self.env['ir.sequence']
        for vals in vals_list:
            if vals.get('sequence', 'Nuevo') == 'Nuevo':
                vals['sequence'] = seq.next_by_code('custodia.service') or 'Nuevo'
            if vals.get('name', 'Nuevo') == 'Nuevo':
                vals['name'] = vals['sequence']
            if not vals.get('state'):
                vals['state'] = 'alerta' if vals.get('request_type', 'alerta') == 'alerta' else 'solicitado'
        return super().create(vals_list)

    def action_convert_to_service(self):
        for rec in self:
            rec._raise_if_missing_service_fields()
            rec.write({
                'request_type': 'servicio',
                'state': 'solicitado',
            })
            rec.message_post(body=_('Alerta convertida a servicio por %s.') % self.env.user.display_name)

    def action_aprobar(self):
        self.write({'state': 'aprobado'})

    def action_asignar(self):
        self.write({'state': 'asignado'})

    def action_ejecutar(self):
        self.write({'state': 'en_ejecucion'})

    def action_finalizar(self):
        self.write({'state': 'finalizado'})

    def action_cancelar(self):
        self.write({'state': 'cancelado'})

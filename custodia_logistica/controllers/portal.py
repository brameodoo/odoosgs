# -*- coding: utf-8 -*-
import json
from datetime import datetime
from urllib.parse import quote_plus

from odoo import fields, http
from odoo.addons.portal.controllers.portal import CustomerPortal
from odoo.exceptions import AccessError, MissingError, ValidationError
from odoo.http import request

def to_int(value):
    """ Función auxiliar para convertir a int de forma segura y evitar errores de base 10 """
    try:
        if value and str(value).strip():
            return int(value)
        return False
    except (ValueError, TypeError):
        return False

class CustodiaPortal(CustomerPortal):

    def _missing_service_fields(self, service):
        if hasattr(service, '_get_missing_service_fields'):
            try:
                return service._get_missing_service_fields()
            except Exception:
                pass

        checks = [
            ('Contacto solicitante', getattr(service, 'contact_id', False)),
            ('Fecha programada', getattr(service, 'start_datetime', False)),
            ('Carrier', getattr(service, 'carrier_id', False)),
            ('Ruta', getattr(service, 'ruta_id', False)),
            ('Nivel de seguridad', getattr(service, 'nivel_seguridad', False)),
            ('Load ID', getattr(service, 'load_id', False)),
        ]
        missing = []
        for label, value in checks:
            if not value:
                missing.append(label)
        return missing

    def _get_portal_service(self, service_id, access_token=None):
        try:
            return self._document_check_access('custodia.service', service_id, access_token)
        except (AccessError, MissingError):
            if access_token:
                raise

        service = request.env['custodia.service'].sudo().browse(service_id)
        if not service.exists():
            raise MissingError()

        if request.env.user._is_public():
            raise AccessError()

        partner = request.env.user.partner_id.commercial_partner_id
        if service.partner_id != partner and not request.env.user.has_group('base.group_user'):
            raise AccessError()
        return service

    def _extract_lat_lng(self, record, lat_names=None, lng_names=None):
        if not record:
            return None
        lat_names = lat_names or ['latitude', 'lat', 'origin_latitude', 'destination_latitude']
        lng_names = lng_names or ['longitude', 'lng', 'lon', 'origin_longitude', 'destination_longitude']
        lat = False
        lng = False
        for name in lat_names:
            if hasattr(record, name):
                lat = getattr(record, name)
                if lat not in (False, None, ''):
                    break
        for name in lng_names:
            if hasattr(record, name):
                lng = getattr(record, name)
                if lng not in (False, None, ''):
                    break
        if lat in (False, None, '') or lng in (False, None, ''):
            return None
        return {'lat': lat, 'lng': lng}

    def _extract_point_from_text(self, value, label=None):
        if not value or ',' not in str(value):
            return None
        try:
            parts = [p.strip() for p in str(value).split(',')]
            if len(parts) < 2:
                return None
            return {'lat': float(parts[0]), 'lng': float(parts[1]), 'label': label}
        except Exception:
            return None

    def _prepare_home_portal_values(self, counters):
        values = super()._prepare_home_portal_values(counters)
        if 'services_count' in counters:
            partner = request.env.user.partner_id.commercial_partner_id
            values['services_count'] = request.env['custodia.service'].sudo().search_count([
                ('partner_id', '=', partner.id)
            ])
        return values

    @http.route(['/custodia/ruta/<int:ruta_id>/coordinates'], type='jsonrpc', auth='public', website=True)
    def get_ruta_coordinates(self, ruta_id, **kwargs):
        ruta = request.env['custodia.ruta'].sudo().browse(ruta_id)
        if not ruta.exists():
            return []

        coords = ruta.get_route_coordinates() if hasattr(ruta, 'get_route_coordinates') else []
        if coords and len(coords) >= 2:
            return coords

        fallback = []
        direct_origin = self._extract_lat_lng(ruta, lat_names=['origin_latitude', 'latitude', 'lat'], lng_names=['origin_longitude', 'longitude', 'lng', 'lon'])
        direct_dest = self._extract_lat_lng(ruta, lat_names=['destination_latitude', 'dest_latitude', 'latitude_destino'], lng_names=['destination_longitude', 'dest_longitude', 'longitude_destino'])
        
        node_origin = self._extract_lat_lng(getattr(ruta, 'nodo_origen_id', False))
        node_dest = self._extract_lat_lng(getattr(ruta, 'nodo_destino_id', False))
        
        text_origin = self._extract_point_from_text(getattr(ruta, 'start_coords', False), 'Origen')
        text_dest = self._extract_point_from_text(getattr(ruta, 'end_coords', False), 'Destino')

        for point, label in [(direct_origin, 'Origen'), (node_origin, 'Origen'), (text_origin, 'Origen'), (direct_dest, 'Destino'), (node_dest, 'Destino'), (text_dest, 'Destino')]:
            if point:
                point.setdefault('label', label)
                exists = any(abs(p['lat'] - point['lat']) < 1e-9 and abs(p['lng'] - point['lng']) < 1e-9 for p in fallback)
                if not exists:
                    fallback.append(point)
        return fallback

    @http.route(['/mis-servicios'], type='http', auth='user', website=True)
    def portal_services(self, **kwargs):
        partner = request.env.user.partner_id.commercial_partner_id
        services = request.env['custodia.service'].sudo().search(
            [('partner_id', '=', partner.id)],
            order='create_date desc'
        )
        return request.render('custodia_logistica.portal_service_list', {
            'services': services,
            'cliente': partner,
            'page_name': 'services',
        })

    @http.route(['/mis-servicios/<int:service_id>'], type='http', auth='public', website=True)
    def portal_service_detail(self, service_id, access_token=None, **kwargs):
        try:
            service = self._get_portal_service(service_id, access_token)
        except (AccessError, MissingError):
            return request.redirect('/mis-servicios')

        return request.render('custodia_logistica.portal_service_detail', {
            'service': service,
            'cliente': service.partner_id,
            'token': service.access_token,
            'pid': request.env.user.partner_id.id if not request.env.user._is_public() else False,
            'page_name': 'service_detail',
            'can_convert_alert': service.request_type == 'alerta',
            'missing_service_fields': self._missing_service_fields(service) if service.request_type == 'alerta' else [],
            'convert_error': kwargs.get('convert_error'),
        })

    @http.route('/custodia/service/<int:service_id>/incidencia', type='jsonrpc', auth='public', methods=['POST'], website=True, csrf=False)
    def custodia_reportar_incidencia(self, service_id, access_token=None, **kwargs):
        mensaje = (kwargs.get('mensaje') or '').strip()
        try:
            service = self._get_portal_service(service_id, access_token)
        except (AccessError, MissingError):
            return {'status': 'error', 'message': 'Acceso denegado.'}

        if not mensaje:
            return {'status': 'error', 'message': 'Debes describir la incidencia.'}

        service.message_post(
            body=f"⚠️ <b>INCIDENCIA REPORTADA:</b><br/>{mensaje}",
            message_type='comment',
            subtype_xmlid='mail.mt_comment'
        )
        return {'status': 'success', 'message': 'Incidencia reportada correctamente.'}

    @http.route(['/mis-servicios/<int:service_id>/convertir'], type='http', auth='user', website=True)
    def portal_convert_alert(self, service_id, access_token=None, **kwargs):
        try:
            service = self._get_portal_service(service_id, access_token)
        except (AccessError, MissingError):
            return request.redirect('/mis-servicios')

        if service.request_type == 'alerta':
            try:
                service.action_convert_to_service()
            except ValidationError as err:
                message = quote_plus(str(err))
                return request.redirect(f'/mis-servicios/{service.id}/editar?access_token={service.access_token}&convert_error={message}')
            service.message_post(body='Alerta convertida a solicitud desde portal por el cliente.')

        return request.redirect(f'/mis-servicios/{service.id}?access_token={service.access_token}')

    @http.route(['/mis-servicios/<int:service_id>/editar'], type='http', auth='user', website=True, methods=['GET', 'POST'])
    def portal_edit_service(self, service_id, access_token=None, **post):
        try:
            service = self._get_portal_service(service_id, access_token)
        except (AccessError, MissingError):
            return request.redirect('/mis-servicios')

        partner = request.env.user.partner_id.commercial_partner_id

        if request.httprequest.method == 'POST':
            vals = {}
            if post.get('contact_id'):
                vals['contact_id'] = to_int(post.get('contact_id'))
            if 'carrier_id' in post:
                vals['carrier_id'] = to_int(post.get('carrier_id'))
            if post.get('start_datetime'):
                new_start_datetime = datetime.strptime(post.get('start_datetime'), '%Y-%m-%dT%H:%M')
                if not service.start_datetime or service.start_datetime != new_start_datetime:
                    vals['start_datetime'] = new_start_datetime
            
            # Otros campos
            for field in ['nivel_seguridad', 'load_id', 'tipo_unidad', 'placas', 'transporte', 'operador1_nombre', 'tel_monitoreo_1']:
                if field in post:
                    vals[field] = post.get(field) or False

            try:
                if vals:
                    service.sudo().write(vals)
                    service.message_post(body='Datos actualizados por cliente desde portal.')
            except ValidationError as err:
                return request.render('custodia_logistica.portal_service_edit', {
                    'service': service,
                    'carriers': request.env['custodia.carrier'].sudo().search([]),
                    'contacts': request.env['res.partner'].sudo().search([('parent_id', '=', partner.id)]),
                    'cliente': partner,
                    'page_name': 'service_edit',
                    'convert_error': str(err),
                    'missing_service_fields': self._missing_service_fields(service) if service.request_type == 'alerta' else [],
                })

            return request.redirect(f'/mis-servicios/{service.id}?access_token={service.access_token}')

        return request.render('custodia_logistica.portal_service_edit', {
            'service': service,
            'carriers': request.env['custodia.carrier'].sudo().search([]),
            'contacts': request.env['res.partner'].sudo().search([('parent_id', '=', partner.id)]),
            'cliente': partner,
            'page_name': 'service_edit',
            'convert_error': post.get('convert_error'),
            'missing_service_fields': self._missing_service_fields(service) if service.request_type == 'alerta' else [],
        })

    @http.route(['/mis-servicios/<int:service_id>/tracking'], type='http', auth='public', website=True, csrf=False)
    def portal_service_tracking(self, service_id, access_token=None, **kwargs):
        try:
            service = self._get_portal_service(service_id, access_token)
        except (AccessError, MissingError):
            return request.make_response(json.dumps({'error': 'Acceso denegado'}), headers=[('Content-Type', 'application/json')])

        data = {
            'lat': service.current_lat or service.ruta_id.origin_latitude,
            'lng': service.current_lng or service.ruta_id.origin_longitude,
            'last_update': str(service.last_update) if service.last_update else 'Sin reportes',
            'state': service.state,
        }
        return request.make_response(json.dumps(data), headers=[('Content-Type', 'application/json')])

    @http.route('/get_nodos_by_maestra/<int:maestra_id>', type='http', auth='user', website=True, csrf=False)
    def get_nodos_by_maestra(self, maestra_id, **kwargs):
        rutas = request.env['custodia.ruta'].sudo().search([('ruta_maestra_id', '=', maestra_id)])
        origenes, destinos = [], []
        seen_orig, seen_dest = set(), set()

        for ruta in rutas:
            if ruta.nodo_origen_id and ruta.nodo_origen_id.id not in seen_orig:
                origenes.append({'id': ruta.nodo_origen_id.id, 'name': ruta.nodo_origen_id.name})
                seen_orig.add(ruta.nodo_origen_id.id)
            if ruta.nodo_destino_id and ruta.nodo_destino_id.id not in seen_dest:
                destinos.append({'id': ruta.nodo_destino_id.id, 'name': ruta.nodo_destino_id.name})
                seen_dest.add(ruta.nodo_destino_id.id)

        data = {'origenes': sorted(origenes, key=lambda x: x['name']), 'destinos': sorted(destinos, key=lambda x: x['name'])}
        return request.make_response(json.dumps(data), headers=[('Content-Type', 'application/json')])

    @http.route(['/solicitar-servicio'], type='http', auth='user', website=True)
    def solicitar_form(self, **kwargs):
        partner = request.env.user.partner_id.commercial_partner_id
        return request.render('custodia_logistica.portal_service_form', {
            'carriers': request.env['custodia.carrier'].sudo().search([]),
            'rutas_maestras': request.env['custodia.ruta.maestra'].sudo().search([]),
            'contacts': request.env['res.partner'].sudo().search([('parent_id', '=', partner.id)]),
            'cliente': partner,
        })

    @http.route(['/solicitar-servicio/submit'], type='http', auth='user', website=True, csrf=True)
    def solicitar_submit(self, **post):
        partner = request.env.user.partner_id.commercial_partner_id
        try:
            start_dt = False
            if post.get('start_datetime'):
                start_dt = datetime.strptime(post['start_datetime'], '%Y-%m-%dT%H:%M')

            contact_id = to_int(post.get('contact_id'))
            if not contact_id or not start_dt:
                raise ValidationError('Debe capturar contacto solicitante y fecha programada.')

            maestra_id = to_int(post.get('ruta_maestra_id'))
            origen_id = to_int(post.get('nodo_origen_id'))
            destino_id = to_int(post.get('nodo_destino_id'))
            carrier_id = to_int(post.get('carrier_id'))

            ruta_variante = request.env['custodia.ruta'].sudo().search([
                ('ruta_maestra_id', '=', maestra_id),
                ('nodo_origen_id', '=', origen_id),
                ('nodo_destino_id', '=', destino_id),
            ], limit=1) if (maestra_id and origen_id and destino_id) else request.env['custodia.ruta']

            vals = {
                'partner_id': partner.id,
                'contact_id': contact_id,
                'carrier_id': carrier_id,
                'ruta_id': ruta_variante.id if ruta_variante else False,
                'start_datetime': start_dt,
                'nivel_seguridad': post.get('nivel_seguridad') or False,
                'load_id': post.get('load_id') or False,
                'tipo_unidad': post.get('tipo_unidad'),
                'placas': post.get('placas'),
                'transporte': post.get('transporte'),
                'operador1_nombre': post.get('operador1_nombre'),
                'tel_monitoreo_1': post.get('tel_monitoreo_1'),
            }

            create_as_service = str(post.get('create_as_service', '')).lower() in ('1', 'true', 'on', 'yes')
            if create_as_service:
                required_for_service = all([vals.get('carrier_id'), vals.get('ruta_id'), vals.get('nivel_seguridad'), vals.get('load_id')])
                vals['request_type'] = 'servicio' if required_for_service else 'alerta'
                vals['state'] = 'solicitado' if required_for_service else 'alerta'
            else:
                vals['request_type'] = 'alerta'
                vals['state'] = 'alerta'

            service = request.env['custodia.service'].sudo().create(vals)
            service._portal_ensure_token()
            return request.redirect(f'/mis-servicios/{service.id}?access_token={service.access_token}')

        except Exception as err:
            return request.render('custodia_logistica.portal_service_form', {
                'carriers': request.env['custodia.carrier'].sudo().search([]),
                'rutas_maestras': request.env['custodia.ruta.maestra'].sudo().search([]),
                'contacts': request.env['res.partner'].sudo().search([('parent_id', '=', partner.id)]),
                'cliente': partner,
                'error': str(err),
            })

    @http.route('/custodia/service/<int:service_id>/<string:action>', type='jsonrpc', auth='public', methods=['POST'], website=True, csrf=False)
    def custodia_action(self, service_id, action, access_token=None, **kwargs):
        try:
            service = self._get_portal_service(service_id, access_token)
        except (AccessError, MissingError):
            return {'status': 'error', 'message': 'No tiene permisos para realizar esta acción.'}

        now = fields.Datetime.now()
        try:
            if action == 'llegada':
                if service.hora_llegada:
                    return {'status': 'error', 'message': 'La llegada ya ha sido registrada anteriormente.'}
                service.write({'hora_llegada': now})
                service.message_post(body=f"✅ <b>Llegada de Custodio:</b> Registrada el {fields.Datetime.to_string(now)}.", subtype_xmlid='mail.mt_note')
                return {'status': 'success', 'message': 'Llegada registrada correctamente.', 'hora_llegada': fields.Datetime.to_string(service.hora_llegada), 'diff_llegada_min': service.diff_llegada_min}
            
            if action == 'iniciar':
                if not service.hora_llegada:
                    return {'status': 'error', 'message': 'Primero debes registrar la llegada del custodio.'}
                if service.hora_inicio_real:
                    return {'status': 'error', 'message': 'El inicio real ya ha sido registrado anteriormente.'}
                service.write({'hora_inicio_real': now, 'state': 'en_ejecucion'})
                service.message_post(body=f"🚀 <b>Servicio Iniciado:</b> Ejecución comenzada el {fields.Datetime.to_string(now)}.", subtype_xmlid='mail.mt_note')
                return {'status': 'success', 'message': 'Inicio real registrado correctamente.', 'hora_inicio_real': fields.Datetime.to_string(service.hora_inicio_real), 'state': service.state}
            
            return {'status': 'error', 'message': 'Acción no reconocida.'}
        except Exception as err:
            return {'status': 'error', 'message': str(err)}

from odoo import models, fields

class CustodiaServiceTracking(models.Model):
    _name = 'custodia.service.tracking'
    _description = 'Tracking GPS Servicio'
    _order = 'create_date asc'

    service_id = fields.Many2one(
        'custodia.service',
        required=True,
        ondelete='cascade'
    )

    latitude = fields.Float(required=True)
    longitude = fields.Float(required=True)
    speed = fields.Float()
    heading = fields.Float()
    device_name = fields.Char()
    timestamp = fields.Datetime(default=fields.Datetime.now)

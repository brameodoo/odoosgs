from odoo import models, fields

class CustodiaUbicacion(models.Model):
    _name = 'custodia.ubicacion'
    _description = 'Ubicaciones Logísticas'
    _rec_name = 'name'
    _order = 'estado, ciudad, name'

    name = fields.Char(string='Nombre', required=True)
    direccion = fields.Char(string='Dirección')
    ciudad = fields.Char(string='Ciudad')
    estado = fields.Selection([
        ('AGU', 'Aguascalientes'),
        ('BCN', 'Baja California'),
        ('BCS', 'Baja California Sur'),
        ('CAM', 'Campeche'),
        ('CDMX', 'Ciudad de México'),
        ('COA', 'Coahuila'),
        ('COL', 'Colima'),
        ('CHP', 'Chiapas'),
        ('CHH', 'Chihuahua'),
        ('DUR', 'Durango'),
        ('GUA', 'Guanajuato'),
        ('GRO', 'Guerrero'),
        ('HID', 'Hidalgo'),
        ('JAL', 'Jalisco'),
        ('MEX', 'Estado de México'),
        ('MIC', 'Michoacán'),
        ('MOR', 'Morelos'),
        ('NAY', 'Nayarit'),
        ('NLE', 'Nuevo León'),
        ('OAX', 'Oaxaca'),
        ('PUE', 'Puebla'),
        ('QRO', 'Querétaro'),
        ('ROO', 'Quintana Roo'),
        ('SLP', 'San Luis Potosí'),
        ('SIN', 'Sinaloa'),
        ('SON', 'Sonora'),
        ('TAB', 'Tabasco'),
        ('TAM', 'Tamaulipas'),
        ('TLX', 'Tlaxcala'),
        ('VER', 'Veracruz'),
        ('YUC', 'Yucatán'),
        ('ZAC', 'Zacatecas'),
    ], string="Estado")

    lat = fields.Float(string='Latitud', digits=(10, 6))
    lng = fields.Float(string='Longitud', digits=(10, 6))

    activa = fields.Boolean(default=True)

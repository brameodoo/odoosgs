# -*- coding: utf-8 -*-
{
    'name': 'MRP Production Custom Labels',
    'version': '19.0.1.0.0',
    'summary': 'Generación y pesaje dinámico de etiquetas por rollo/caja en Órdenes de Fabricación',
    'author': 'Desarrollador Odoo',
    'category': 'Manufacturing/Manufacturing',
    'sequence': 10,
    'depends': [
        'mrp',
        'barcodes',
        'sale_management',
    ],
    'data': [
        # 1. Seguridad y Acceso a Modelos
        'security/ir.model.access.csv',
        
        # 2. Secuencias y Datos Iniciales
        'data/ir_sequence_data.xml',
        
        # 3. Vistas de Wizards / Asistentes (Deben cargarse ANTES de ser llamadas en mrp_production)
        'wizard/mrp_production_label_wizard_views.xml',
        'wizard/mrp_label_reprint_wizard_views.xml',
        
        # 4. Vistas Principales
        'views/mrp_workcenter_views.xml',
        'views/product_template_views.xml',
        'views/mrp_production_views.xml',
        
        # 5. Reportes e Impresiones ZPL / PDF
        'report/mrp_packaging_label_reports.xml',
        'report/report_roll_label_zpl.xml',
        'report/report_box_label_zpl.xml',
        'report/report_pallet_master_zpl.xml',
        'report/report_packing_list_pdf.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}

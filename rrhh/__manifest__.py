# -*- coding: utf-8 -*-
{
    'name': "RRHH",

    'summary': """ Módulo de RRHH para Guatemala """,

    'description': """
        Módulo de RRHH para Guatemala
    """,

    'author': "Rodolfo Borstcheff",
    'website': "http://www.aquih.com",

    'category': 'Uncategorized',
    'version': '0.1',

    'depends': ['base', 'hr', 'hr_contract','hr_payroll_account'],

    'data': [
        'data/rrhh_data.xml',
        'data/paperformat_libro_salarios.xml',
        'data/hr_payroll_expense_data.xml',
        'views/hr_views.xml',
        'views/hr_contract_views.xml',
        'views/hr_payroll_views.xml',
        'views/planilla_views.xml',
        'views/res_company_views.xml',
        'views/report.xml',
        'views/recibo.xml',
        'wizard/planilla_pdf.xml',
        'wizard/planilla.xml',
        'views/libro_salarios.xml',
        'views/hr_work_entry_views.xml',
        'wizard/rrhh_libro_salarios_view.xml',
        'wizard/rrhh_informe_empleador_view.xml',
        'wizard/igss.xml',
        'wizard/cerrar_nominas.xml',
        'security/ir.model.access.csv',
    ],
}

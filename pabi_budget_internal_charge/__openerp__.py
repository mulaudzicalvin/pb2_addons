# -*- coding: utf-8 -*-
{
    'name': "NSTDA :: PABI2 Internal Charge",
    'summary': "",
    'author': "Ecosoft",
    'website': "http://ecosoft.co.th",
    'category': 'Account',
    'version': '0.1.0',
    'depends': [
        'hr_expense_auto_invoice',
        'pabi_budget_plan',
    ],
    'data': [
        'wizard/cost_control_breakdown_wizard.xml',
        'views/budget_plan_unit_view.xml',
        'views/hr_expense_view.xml',
    ],
    'demo': [
    ],
    'installable': True,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

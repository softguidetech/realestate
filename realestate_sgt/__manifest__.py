# -*- coding : utf-8 -*-

{
    'name': 'Real Estate',
    'author': "Soft Guide Technology",
    'version': '16.0.1.4',
    'price': 239.00,
    'currency': "EUR",
    # 'live_test_url':'https://youtu.be/qp0V-bN-Poo',
    "images":['static/description/icon.png'],
    'summary': 'Apps for sale property management rent property management real estate property management real estate lease management property lease management property booking property rental property rental invoice housing rental housing lease house rental',
    'description': "Sale & Rent property management ,create contract, renew contract, allow partial payment for sale property and invoice due date auto generate between one month interval, maintain property maintenance, user commission calculate at register payment time base on property, automatically generate commission worksheet at last of day of the month. view and print contract expired report, property analysis report.",
    'depends': ['product', 'analytic', 'sale', 'account', 'stock', 'repair', 'portal','report_xlsx'],
    "license": "OPL-1",
    'data': [
        'data/ir_sequence_data.xml',
        'data/property_reminder.xml',
        'data/property_mail_template.xml',
        'wizard/reserved_unit_report_wizard.xml',
        'wizard/contract_termination_wizard.xml',
        'security/ir_module_category_data.xml',
        'security/ir.model.access.csv',
        'views/res_company.xml',
        'views/configuration.xml',
        "views/account_payment_views.xml",
        'views/maintanance.xml',
        'views/property_purchase.xml',
        'views/property_reserve.xml',
        'views/contract_details.xml',
        'views/renew_contract.xml',
        'views/commission.xml',
        'views/property_product.xml',
        'views/property_partners.xml',
        'views/property_offer.xml',
        'views/property_search.xml',
        'views/unit_search.xml',
        'views/property_floor.xml',
        'views/account_move.xml',
        'views/property_unit.xml',
        'views/property_menu.xml',
        'views/repair_order.xml',
        'views/real_estate_portal_template.xml',
        'report/report_header.xml',
        'report/contract_template.xml',
        "report/report_pdc_payment.xml",
        'report/contract_details_template.xml',
        'report/report.xml',
        'report/invoice_report_inherit.xml',
        # 'views/configuration.xml',
        'views/res_config_setting.xml',

    ],

    'qweb': ['static/src/xml/*.xml'],
    'demo': [],
    'installable': True,
    'auto_install': False,
    # 'price': 79,
    # 'currency': "EUR",
    'category': 'Sales',
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

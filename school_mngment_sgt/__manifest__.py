# -*- coding: utf-8 -*-


{
    'name': 'School Management SGT',
    'version': '16.0.1.0.0',
    'category': 'School Management',
    'summary': 'A Module For School Management',
    'author': 'SGT',
    'website': "http://www.softguidetech.com",
    "depends": ["hr", "crm", "account"],
    'data': [
        "security/school_security.xml",
        "security/ir.model.access.csv",
        "data/student_sequence.xml",
        "data/mail_template.xml",
        "wizard/terminate_reason_view.xml",
        "views/student_view.xml",
        "views/school_view.xml",
        "views/teacher_view.xml",
        "views/parent_view.xml",
        "wizard/assign_roll_no_wizard.xml",
        "wizard/move_standards_view.xml",
        "report/report_view.xml",
        "report/identity_card.xml",
        "report/teacher_identity_card.xml",
    ],
    "demo": ["demo/school_demo.xml"],
    "assets": {
        "web.assets_backend": ["/school_mngment_sgt/static/src/scss/schoolcss.scss"]
    },
    "installable": True,
    "application": True,
    "images": ['static/description/icon.png'],
}

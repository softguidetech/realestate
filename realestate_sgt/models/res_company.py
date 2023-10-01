# -*- coding: utf-8 -*-
from odoo import models, fields, api, _


class ResCompany(models.Model):
    _inherit = 'res.company'

    fax = fields.Char(string="FAX")
    po_box = fields.Char(string="P.O.Box")
    fax_arabic = fields.Char(string="FAX(Arabic)")
    po_box_arabic = fields.Char(string="P.O.Box(Arabic)")
    country_arabic = fields.Char(string="Country(Arabic)")
    tel_arabic = fields.Char(string="Phone(Arabic)")
    is_real_estate_company = fields.Boolean(string='Is Real Estate Company')
    contract_value = fields.Float(string='Contract Value', digits=(16, 3), store=True)
    contract_partner_id = fields.Many2one('res.partner', string='Contract Partner')
    # , domain = ([('partner_type', 'in', ('renter', 'purchaser'))])
    deposit_account_id = fields.Many2one('account.account', string='Deposit Account', help='The deposit account for the company')
    debit_account_id = fields.Many2one('account.account', string='Debit Account', help='The debit account for the company')
    credit_account_id = fields.Many2one('account.account', string='Credit Account', help='The credit account for the company')


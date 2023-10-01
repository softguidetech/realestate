# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError
from datetime import date,timedelta
from dateutil import relativedelta



class PropertFloor(models.Model):
    _name = 'property.floor'

    def _default_currency(self):
        return self.env.user.company_id.currency_id

    def _default_company(self):
        return self.env.user.company_id

    name = fields.Char(string='Floor Ref',)
    code = fields.Char(string='Floor Code',)
    number_of_unit = fields.Char(string='Floor Number of units',)
    note = fields.Char(string='Note',)
    company_id = fields.Many2one('res.company', default=_default_company)
    currency_id = fields.Many2one('res.currency', default=_default_currency)
    property_id = fields.Many2one('product.product',string='Property',domain=[('is_property','=',True)])
    floor_area_feet = fields.Integer(string='Floor Area feet',)
    floor_area_meter = fields.Integer(string='Floor Area meter',)
    floor_rent_value = fields.Monetary(string='Floor Rent Value / Yearly',)
    state = fields.Selection([('draft','draft'),('register','Registered')],default='draft')
    analytic_account_id = fields.Many2one('account.analytic.account', string="Analytic Account", )
    account_id = fields.Many2one('account.account', string="Income Account", )
    unit_ids = fields.One2many('property.unit', 'floor_id', string='Units')

    def confirm(self):
        for rec in self:
            rec.write({
                'state': 'register',
                       })

    def reset(self):
        for rec in self:
            rec.write({
                'state': 'draft',
                       })
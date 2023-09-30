# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError
from datetime import date,timedelta
from dateutil import relativedelta
from odoo.tools.float_utils import float_round



class PropertyFloor(models.Model):
    _name = 'property.unit'

    def _default_currency(self):
        return self.env.user.company_id.currency_id

    def _default_company(self):
        return self.env.user.company_id

    name = fields.Char(string='Unit Ref',)
    code = fields.Char(string='Unit Code',)
    note = fields.Char(string='Note',)
    company_id = fields.Many2one('res.company',default=_default_company)
    currency_id = fields.Many2one('res.currency',default=_default_currency)
    floor_id = fields.Many2one('property.floor',string='Floor')
    property_id = fields.Many2one('product.product',string='Property',domain=[('is_property','=',True)])
    unit_area_feet = fields.Float(string='Unit Area feet',)
    unit_area_meter = fields.Float(string='Unit Area meter',)
    unit_rent_value = fields.Monetary(string='Unit Rent Value / Yearly')
    state = fields.Selection([('draft','Draft'),('rent','Rentable'),('sale','Saleable'),('reserve','Reserve'),('sold','Sold'),('cancel','Cancelled')], default='draft', string="Property Status", help='State of the Property')
    renter_history_ids = fields.One2many('renter.history', 'unit_id' )
    property_book_for = fields.Selection([('sale','Sale'),('rent','Rent')], string=" Unit Type", help="Unit reserve for rent or sale.")
    deposit = fields.Monetary("Deposit")
    monthly_rent = fields.Float("Monthly Rent", compute='_compute_total',digits=(16, 3), store=True)
    rent_offer_ids = fields.One2many('property.rent.offer','property_id')
    document_ids = fields.Many2many('unit.document','unit_document_default_rel','unit_id','document_id')
    is_reserved = fields.Boolean()
    user_id = fields.Many2one('res.users', string="Login User")
    analytic_account_id = fields.Many2one('account.analytic.account', string="Analytic Account",)
    account_id = fields.Many2one('account.account', string="Income Account",)
    user_commission_ids = fields.One2many('user.commission', 'unit_id', string="Commission" )
    invoice_count = fields.Integer("#Invoice", compute='_compute_invoice_count')
    contract_count = fields.Integer("#Contract", compute='_compute_contract_count')
    owner_id = fields.Many2one('res.partner', string='Unit Owner')
    dewa_number = fields.Char(string='Water and Elec Number')
    is_contract_expired = fields.Boolean(string="Is Expired", compute='_compute_is_expired')
    classification_id = fields.Many2one('unit.classification', string='Classification')

    def _compute_is_expired(self):
        for rec in self:
            rec.is_contract_expired = False
            if rec.state == 'reserve':
                contract_id = self.env['contract.details'].search([('unit_id', '=', rec.id),('state', '=', 'expire')])
                if contract_id:
                    rec.is_contract_expired = True

    def renew_unit(self):
        if self.state == 'reserve' and self.is_contract_expired == True:
            if self.renter_history_ids:
                if all(each.state == 'reserve' for each in self.renter_history_ids):
                    raise UserError(_("This property already reserved..!"))
            if not self.analytic_account_id or not self.account_id:
                raise UserError(_("Please enter analytic account or income account ..!"))
            view_id = self.env.ref('property_rental_mgt_app.property_book_wizard')

            # offer
            offer_price = 0
            discount_offer = 0
            offer_name = ''
            if self.rent_offer_ids:
                for line in self.rent_offer_ids:
                    if line.state == 'open' and line.start_date <= fields.Date.today() and line.end_date >= fields.Date.today():
                        if line.discount_offer > 0:
                            offer_name = line.name + ' ' + str(line.discount_offer) + '%' + ' off'
                            discount_offer = line.discount_offer
            if view_id:
                book_property_data = {
                    'name': _('Reserve unit & Contract Configure'),
                    'type': 'ir.actions.act_window',
                    'view_type': 'form',
                    'view_mode': 'form',
                    'res_model': 'property.book',
                    'view_id': view_id.id,
                    'target': 'new',
                    'context': {
                        'property_id': self.property_id.id,
                        'unit_id': self.id,
                        'desc': self.note,
                        'rent_price': self.unit_rent_value,
                        'renter_id': self.property_id.renter_id.id,
                        'owner_id': self.property_id.owner_id.id,
                        'monthly_rent': self.monthly_rent,
                        # 'offer_price':offer_price,
                        'discount_offer': discount_offer,
                        'offer_name': offer_name,
                        'from_reserve_property': False
                    },
                }
                # self.write({
                #     'state': 'reserve'
                # })
            return book_property_data
#
        # else:
        #     raise UserError(_("The unit cannot be renewed in its current state or contract status."))

    @api.depends('unit_rent_value')
    def _compute_total(self):
        for rec in self:
            if rec.unit_rent_value != 0:
                # rec.monthly_rent = round(rec.unit_rent_value / 12)
                rec.monthly_rent = float_round(rec.unit_rent_value/12, precision_digits=3)
            else:
                rec.monthly_rent = 0

    def button_confirm(self):
        if self.state == 'draft' and self.property_book_for == 'sale':
            if self.unit_rent_value <= 0 or self.discounted_price <= 0:
                raise UserError(_("Please enter valid unit price or reasonable amount...!"))
            self.state = 'sale'
            # if self.state == 'draft' and self.property_book_for == 'rent':
            #     if self.rent_price <= 0 or self.deposite <= 0:
            #         raise UserError(_("Please enter valid property rent amount...!"))
        contracts = self.env['contract.contract'].search([])
        if not contracts:
            raise UserError(_("Please first create contract type from property configuration -> contract...!"))
        self.state = 'rent'

        if self.user_commission_ids:
            for each in self.user_commission_ids:
                if each.percentage <= 0:
                    raise UserError(_("Please enter valid commission percentage in commission lines...!"))

    # def reset(self):
    #     # for rec in self:
    #     #     rec.write({
    #     #         'state': 'draft',
    #     #                })
    #     pass

    def reset_to_draft(self):
        if self.state == 'rent':
            self.write({'state': 'draft'})
        else:
            raise UserError(_("You cannot reset unit if it is not in rent state!"))

    # def renew_contract(self):
    #     # Add logic here to renew the contract
    #     # This method should update the contract or create a new one based on your requirements
    #     return True

    def reserve_property(self):
        if self.renter_history_ids:
            if all(each.state == 'reserve' for each in self.renter_history_ids):
                raise UserError(_("This property already reserved..!"))
        if not self.analytic_account_id or not self.account_id:
            raise UserError(_("Please enter analytic account or income account ..!"))
        # if self.property_book_for != 'rent':
        #     raise UserError(_("This property only allow for sale..!"))
        # if self.unit_rent_value <= 0 or self.deposit <= 0:
        #     raise UserError(_("Please enter valid unit rent or deposit price for (%s)..!") % self.name)
        view_id = self.env.ref('property_rental_mgt_app.property_book_wizard')

        # offer
        offer_price = 0
        discount_offer = 0
        offer_name = ''
        if self.rent_offer_ids:
            for line in self.rent_offer_ids:
                if line.state == 'open' and line.start_date <= fields.Date.today() and line.end_date >= fields.Date.today():
                    if line.discount_offer > 0:
                        offer_name = line.name + ' ' + str(line.discount_offer) + '%' + ' off'
                        discount_offer = line.discount_offer
        if view_id:

            book_property_data = {
                'name': _('Reserve unit & Contract Configure'),
                'type': 'ir.actions.act_window',
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'property.book',
                'view_id': view_id.id,
                'target': 'new',
                'context': {
                    'property_id': self.property_id.id,
                    'unit_id': self.id,
                    'desc': self.note,
                    'rent_price': self.unit_rent_value,
                    'renter_id': self.property_id.renter_id.id,
                    'owner_id': self.property_id.owner_id.id,
                    'monthly_rent': self.monthly_rent,
                    # 'offer_price':offer_price,
                    'discount_offer': discount_offer,
                    'offer_name': offer_name,
                    'from_reserve_property': True
                },
            }
            # self.write({
            #     'state': 'reserve'
            # })
        return book_property_data

    @api.depends()
    def _compute_invoice_count(self):
        for rec in self:
            # invoices = self.renter_history_ids.filtered(lambda p: p.is_invoice == True)
            invoices = self.env['account.move'].search([('unit_id', '=', self.id)])
            rec.invoice_count = len(invoices)

    @api.depends()
    def _compute_contract_count(self):
        for rec in self:
            contracts = self.env['contract.details'].search([('unit_id', '=', rec.id)])
            rec.contract_count = len(contracts)

    # Define the action to navigate to invoices related to this unit
    def action_view_invoice(self):
        # invoices = self.mapped('renter_history_ids').filtered(lambda p: p.is_invoice)
        invoices = self.env['account.move'].search([('unit_id', '=', self.id)])
        action = self.env.ref('account.action_move_out_invoice_type').sudo().read()[0]
        if len(invoices) > 1:
            action['domain'] = [('id', 'in', invoices.ids)]
        elif len(invoices) == 1:
            action['views'] = [(self.env.ref('account.view_move_form').id, 'form')]
            action['res_id'] = invoices.ids[0]
        else:
            action = {'type': 'ir.actions.act_window_close'}
        return action


    def action_view_contracts(self):
        contracts = self.env['contract.details'].search([('unit_id', '=', self.id)])
        action = self.env.ref('property_rental_mgt_app.action_contract_details').sudo().read()[0]
        if len(contracts) > 1:
            action['domain'] = [('id', 'in', contracts.ids)]
        elif len(contracts) == 1:
            action['views'] = [(self.env.ref('property_rental_mgt_app.property_contract_details_form').id, 'form')]
            action['res_id'] = contracts.ids[0]
        else:
            action = {'type': 'ir.actions.act_window_close'}
        return action
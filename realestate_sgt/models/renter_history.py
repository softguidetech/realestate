# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError

class RentPayerHistory(models.Model):
    _name = 'renter.history'
    _description = "Renter History"

    renter_id = fields.Many2one('res.partner', string="Renter")
    date = fields.Date("Current Date")
    from_date = fields.Date()
    to_date = fields.Date()
    rent_price = fields.Float("Property Rent")
    state = fields.Selection([('avl','Available'),('reserve','Reserve'),('cancel','Cancelled')], string="Status", default='avl')
    owner_id = fields.Many2one('res.partner', string="Property Owner")
    property_id = fields.Many2one('product.product')
    unit_id = fields.Many2one('property.unit',string='Unit')

    invoice_id = fields.Many2one('account.move', string='Invoice')
    is_invoice =fields.Boolean()
    reference = fields.Char()
    deposite = fields.Float()
    contract_month = fields.Integer("Contract Month")
    contract_id = fields.Many2one('contract.details','Contract')
    salesperson_id = fields.Many2one('res.users', string="Salesperson",default=lambda self: self.env.user)
    discount_offer = fields.Float("Discount Offer (%)")
    offer_price = fields.Float("Offer Amount")

    def create_rent_invoice(self):
        account_inv_obj = self.env['account.move']
        product_id = self.property_id
        # Search for the income account
        if product_id.property_account_income_id:
            income_account = product_id.property_account_income_id.id
        elif product_id.categ_id.property_account_income_categ_id:
            income_account = product_id.categ_id.property_account_income_categ_id.id
        else:
            raise UserError(_('Please define income '
                              'account for this product: "%s" (id:%d).')
                            % (product_id.name, product_id.id))
        # offer
        p_name = ''
        if self.offer_price > 0 and self.property_id.rent_offer_ids:
            price_unit = self.offer_price
            p_name = self.property_id.name 
        else:
            price_unit = self.deposite
            p_name = self.property_id.name + ' / ' + self.unit_id.name

        # Create an empty dictionary for analytic values
        analytic_vals = {}

        # Check if the property has an analytic account
        if self.property_id.analytic_account_id:
            analytic_account_id = self.property_id.analytic_account_id.id
            analytic_vals[analytic_account_id] = 100

        # Check if the floor has an analytic account
        if self.unit_id.floor_id.analytic_account_id:
            floor_analytic_account_id = self.unit_id.floor_id.analytic_account_id.id
            analytic_vals[floor_analytic_account_id] = 100

        # Check if the unit has an analytic account
        if self.unit_id.analytic_account_id:
            unit_analytic_account_id = self.unit_id.analytic_account_id.id
            analytic_vals[unit_analytic_account_id] = 100

        vals = {
            'property_id': self.property_id.id,
            'unit_id': self.unit_id.id,
            'contract_id': self.contract_id.id if self.contract_id else False,
            'move_type': 'out_invoice',
            'invoice_origin': self.property_id.name + ' / ' + self.unit_id.name,
            'partner_id': self.renter_id.id,
            'invoice_user_id': self.salesperson_id.id or self.property_id.salesperson_id.id,
            'invoice_line_ids': [(0, 0, {
                'name': p_name,
                'product_id': self.property_id.id,
                'account_id': income_account,
                'analytic_distribution': analytic_vals,
                'price_unit': price_unit})],
        }

        if self.rent_price <= 0:
            raise UserError(
                _("You will not buy this property, (%s) because this property price is zero.") % self.property_id.name)

        invoice_id = account_inv_obj.create(vals)
        if invoice_id:
            self.write({'invoice_id': invoice_id.id, 'state': 'reserve', 'is_invoice': True})

        return {
            'name': 'Partial Payment Invoice',
            'type': 'ir.actions.act_window',
            'view_mode': 'tree,form',
            'res_id': invoice_id.id,
            'views': [(self.env.ref('account.view_move_form').id, 'form')],
            'res_model': 'account.move',
            'domain': [('id', '=', invoice_id.id)],
        }

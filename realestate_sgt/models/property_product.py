# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

from datetime import date, timedelta
from dateutil import relativedelta


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    is_property = fields.Boolean(string="Property", compute='_compute_is_property')

    @api.depends('product_variant_id')
    def _compute_is_property(self):
        for p in self:
            p.is_property = p.product_variant_id[:1].is_property

    @api.depends('product_variant_id')
    def _compute_product_variant_id(self):
        for p in self:
            p.is_property = p.product_variant_id[:1].is_property


class ProductProduct(models.Model):
    _inherit = 'product.product'

    def _default_company_id(self):
        return self.env.user.company_id

    @api.model
    def default_get(self, fields):
        defaults = super(ProductProduct, self).default_get(fields)
        defaults['company_id'] = self._default_company_id()
        return defaults

    invoice_count = fields.Integer("#Invoice", compute='_compute_invoice_count')
    contract_count = fields.Integer("#Contract", compute='_compute_contract_count')
    maintain_count = fields.Integer("#Maintain", compute='_compute_maintanance')
    is_property = fields.Boolean(string="Property")
    deposite = fields.Float("Monthly Rent")
    maintain_charge = fields.Float("Maintenance Charge")
    reasonable_price = fields.Boolean("Allow Discount(%)")
    owner_id = fields.Many2one('res.partner', string="Property Owner")
    renter_id = fields.Many2one('res.partner', string="Property Renter")
    purchaser_id = fields.Many2one('res.partner', string="Property Purchaser")
    renter_rel_id = fields.Many2one(related='renter_id', string="Property Renter ")
    purchaser_rel_id = fields.Many2one(related='purchaser_id', string="Property Purchaser ")
    user_id = fields.Many2one('res.users', string="Login User")
    salesperson_id = fields.Many2one('res.users', string="Salesperson", default=lambda self: self.env.user)
    facility_ids = fields.Many2many('property.facility', string="Facility & Services")
    property_book_for = fields.Selection([('sale', 'Sale'), ('rent', 'Rent')], default='rent', string=" Property Type",
                                         help="property reserve for rent and sale.")
    property_type = fields.Many2one('property.type')
    rent_price = fields.Float("Property Rent")
    reasonable_rent = fields.Boolean("Allow Discount in(%)")
    discounted_price = fields.Float("Reasonable Price")
    property_price = fields.Float()
    partial_payment_ids = fields.Many2many('partial.payment', 'property_partial_payment',
                                           string='Allow Partial Payment')
    user_commission_ids = fields.One2many('user.commission', 'property_id', string="Commission")
    renter_history_ids = fields.One2many('renter.history', 'property_id')
    state = fields.Selection(
        [('draft', 'Draft'), ('rent', 'Rentable'), ('sale', 'Saleable'), ('reserve', 'Reserve'), ('sold', 'Sold'),
         ('cancel', 'Cancelled')], string="Property Status", help='State of the Property')
    property_floor = fields.Integer()
    carpet_area = fields.Char("Carpet Area")
    build_area = fields.Char("Build-up Area")
    construction_status = fields.Char("Construction Status", default="Ready to Move")
    plot_area = fields.Char()
    invoice_ids = fields.Many2many('account.move', 'partial_payment_account_invoice')
    location = fields.Char("Address")
    city = fields.Char()
    street = fields.Char()
    zipcode = fields.Integer("Zip")
    state_id = fields.Many2one('res.country.state', string="State")
    country_id = fields.Many2one('res.country', string="Country")
    phone = fields.Char("Phone")
    bedrooms = fields.Char()
    balconies = fields.Integer()
    washroom = fields.Integer()
    more_details = fields.Text("More Details")
    rent_unit = fields.Selection([('monthly', 'Monthly'), ('yearly', 'Yearly')], default='monthly')
    property_avl_from = fields.Date("Property Exist From")
    is_partial = fields.Boolean()
    is_reserved = fields.Boolean()
    is_sold = fields.Boolean()
    age = fields.Integer('Property Age')
    months = fields.Integer('Months')
    reasonable_percent = fields.Float("Reasonable Rent Percentage")
    reasonable_price_per = fields.Float("Reasonable Price Percentage")
    document_ids = fields.Many2many('property.document', 'property_document_default_rel', 'property_id', 'document_id')
    image_ids = fields.Many2many('property.image', 'property_image_default_rel', 'property_id', 'image_id',
                                 string="Images")
    rent_offer_ids = fields.One2many('property.rent.offer', 'property_id')
    sale_offer_ids = fields.One2many('property.sale.offer', 'property_id')
    property_search_id = fields.Many2one('property.search')
    allow_delay_fine = fields.Boolean("Allow Delay Payment Fine?")
    delay_fine_id = fields.Many2one('delay.fine', string="Delay Payment Fine")
    #
    floor_ids = fields.One2many('property.floor', 'property_id', string='Floors')
    unit_ids = fields.One2many('property.unit', 'property_id', string='Units')
    analytic_account_id = fields.Many2one('account.analytic.account', string="Analytic Account", )
    account_id = fields.Many2one('account.account', string="Income Account", )
    dewa_number = fields.Char(string='Water and Elec Number')
    property_value = fields.Char(string='Property Value')
    user_groups_not_allowed = fields.Boolean(
        string='User Groups Not Allowed',
        compute='_compute_user_groups_not_allowed',
        store=False
    )
    is_real_estate_company = fields.Boolean(string='Is Real Estate Company',
                                            related='company_id.is_real_estate_company')

    def _compute_user_groups_not_allowed(self):
        for record in self:
            user = self.env.user
            # Check if the user does not belong to the specified groups
            if not user.has_group('realestate_sgt.group_rent_payer') and \
                    not user.has_group('realestate_sgt.group_purchaser') and \
                    not user.has_group('realestate_sgt.group_manager'):
                record.user_groups_not_allowed = True
            else:
                record.user_groups_not_allowed = False

    def unlink(self):
        for line in self:
            if line.state != 'draft':
                raise ValidationError(_('You cannot delete Sale And Rent Property (name: %s)') % (line.name,))
        return super(ProductProduct, self).unlink()

    @api.onchange('state_id')
    def get_country(self):
        if self.state_id:
            self.country_id = self.state_id.country_id

    @api.onchange('property_avl_from')
    def culculate_age(self):
        if self.property_avl_from:
            if self.property_avl_from > date.today():
                return {
                    'warning': {'title': 'Warning!', 'message': 'Please enter valid property exist date...!'},
                    'value': {'property_avl_from': None}
                }
            self.age = 0
            self.months = 0
            days_in_year = 365
            year = int((date.today() - self.property_avl_from).days / days_in_year)
            result = relativedelta.relativedelta(fields.Date.today(), self.property_avl_from)
            months = result.months + (12 * result.years)
            if year > 0:
                self.age = year
            else:
                self.months = months

    def button_confirm(self):
        if self.state == 'draft' and self.property_book_for == 'sale':
            if self.property_price <= 0 or self.discounted_price <= 0:
                raise UserError(_("Please enter valid property price or reasonable amount...!"))
            self.state = 'sale'
        if self.state == 'draft' and self.property_book_for == 'rent':
            # if self.rent_price <= 0 or self.deposite <= 0:
            #     raise UserError(_("Please enter valid property rent amount...!"))
            contracts = self.env['contract.contract'].search([])
            if not contracts:
                raise UserError(_("Please first create contract type from property configuration -> contract...!"))
            self.state = 'rent'

        if self.user_commission_ids:
            for each in self.user_commission_ids:
                if each.percentage <= 0:
                    raise UserError(_("Please enter valid commission percentage in commission lines...!"))

    def button_set_to_draft(self):
        if self.state in ['rent', 'sale']:
            self.state = 'draft'

    @api.onchange('state')
    def change_state(self):
        if self.renter_history_ids or self.invoice_ids:
            raise UserError(_("You can not move this property(%s) in another state..!") % self.name)
        if self.state == 'sale':
            self.property_book_for = 'sale'
        elif self.state == 'rent':
            self.property_book_for = 'rent'

    @api.onchange('reasonable_percent', 'reasonable_rent', 'rent_price')
    def calculate_reasonable_rent(self):
        if self.reasonable_rent:
            if self.reasonable_percent > 0:
                discount = (self.rent_price * self.reasonable_percent) / 100
                self.deposite = self.rent_price - discount
            else:
                self.deposite = self.rent_price
        else:
            self.deposite = self.rent_price

    @api.onchange('reasonable_price_per', 'reasonable_price', 'property_price')
    def calculate_reasonable_price(self):
        if self.reasonable_price:
            if self.reasonable_price_per > 0:
                discount = (self.property_price * self.reasonable_price_per) / 100
                self.discounted_price = self.property_price - discount
            else:
                self.discounted_price = self.property_price
        else:
            self.discounted_price = self.property_price

    @api.depends()
    def _compute_invoice_count(self):
        for rec in self:
            invoices = self.env['account.move'].search([('property_id', '=', rec.id)])
            rec.invoice_count = len(invoices)

    @api.depends()
    def _compute_contract_count(self):
        for rec in self:
            contracts = self.env['contract.details'].search([('property_id', '=', rec.id)])
            rec.contract_count = len(contracts)

    @api.depends()
    def _compute_maintanance(self):

        for rec in self:
            maintanance = self.env['property.maintanance'].search([('property_id', '=', rec.id)])
            rec.maintain_count = len(maintanance)

    def buy_now_property(self):
        if self.invoice_ids:
            if any(inv.state == 'paid' for inv in self.invoice_ids):
                raise UserError(_("This property (%s) already sold out..!") % self.name)
        if self.property_book_for != 'sale':
            raise UserError(_("This property only allow for Rent..!"))
        if self.property_price < 1:
            raise UserError(_("Please enter valid property price for (%s)..!") % self.name)

        view_id = self.env.ref('realestate_sgt.property_buy_wizard')
        if self.reasonable_price and self.reasonable_price_per > 0:
            property_price = self.discounted_price
        else:
            property_price = self.property_price

        # offer
        offer_price = 0
        discount_offer = 0
        offer_name = ''
        if self.sale_offer_ids:
            for line in self.sale_offer_ids:
                if line.state == 'open' and line.start_date <= fields.Date.today() and line.end_date >= fields.Date.today():
                    if line.discount_offer > 0:
                        offer_price = line.offer_price
                        offer_name = line.name + ' ' + str(line.discount_offer) + '%' + ' off'
                        discount_offer = line.discount_offer
        if view_id:
            buy_property_data = {
                'name': _('Purchase Property & Partial Payment'),
                'type': 'ir.actions.act_window',
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'property.buy',
                'view_id': view_id.id,
                'target': 'new',
                'context': {
                    'property_id': self.id,
                    'desc': self.more_details,
                    'property_price': property_price,
                    'owner_id': self.owner_id.id,
                    'purchaser_id': self.purchaser_id.id,
                    'offer_price': offer_price,
                    'discount_offer': discount_offer,
                    'offer_name': offer_name
                },
            }
        return buy_property_data

    def reserve_property(self):
        if self.renter_history_ids:
            if all(each.state == 'reserve' for each in self.renter_history_ids):
                raise UserError(_("This property already reserved..!"))

        if self.property_book_for != 'rent':
            raise UserError(_("This property only allow for sale..!"))
        if self.rent_price <= 0 or self.deposite <= 0:
            raise UserError(_("Please enter valid property rent or deposite price for (%s)..!") % self.name)
        view_id = self.env.ref('realestate_sgt.property_book_wizard')

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
                'name': _('Reserve Property & Contract Configure'),
                'type': 'ir.actions.act_window',
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'property.book',
                'view_id': view_id.id,
                'target': 'new',
                'context': {
                    'property_id': self.id,
                    'desc': self.more_details,
                    'rent_price': self.rent_price,
                    'renter_id': self.renter_id.id,
                    'owner_id': self.owner_id.id,
                    'monthly_rent': self.deposite,
                    # 'offer_price':offer_price,
                    'discount_offer': discount_offer,
                    'offer_name': offer_name
                },
            }
        return book_property_data

    def action_view_invoice(self):
        for rec in self:
            invoices = self.env['account.move'].search([('property_id', '=', rec.id)])
            action = self.env.ref('account.action_move_out_invoice_type').read()[0]
            if len(invoices) > 1:
                action['domain'] = [('id', 'in', invoices.ids)]
            elif len(invoices) == 1:
                action['views'] = [(self.env.ref('account.view_move_form').id, 'form')]
                action['res_id'] = invoices.ids[0]
            else:
                action = {'type': 'ir.actions.act_window_close'}
            return action

    def action_view_maintenance(self):
        for rec in self:
            invoices = self.env['property.maintanance'].search([('property_id', '=', rec.id)])
            action = self.env.ref('realestate_sgt.action_maintanance').read()[0]
            if len(invoices) > 1:
                action['domain'] = [('id', 'in', invoices.ids)]
            elif len(invoices) == 1:
                action['views'] = [(self.env.ref('realestate_sgt.property_maintanance_form').id, 'form')]
                action['res_id'] = invoices.ids[0]
            else:
                action = {'type': 'ir.actions.act_window_close'}
            return action

    # automatically set property to rentable state
    def property_set_to_available(self):
        contracts = self.env['contract.details'].search([('property_id', '=', self.id)])
        if all(c.state == "expire" for c in contracts):
            self.write({'state': "rent"})

    def auto_deduct_fine_on_delay_payment(self):
        invoices = self.env['account.move'].search(
            [('property_id', '!=', False), ('invoice_date_due', '!=', False), ('payment_state', '=', 'not_paid')])
        if invoices:
            product_id = invoices[0].property_id
        else:
            product_id = self.env['product.product'].search([], limit=1)

        if product_id.property_account_income_id:
            income_account = product_id.property_account_income_id.id
        elif product_id.categ_id.property_account_income_categ_id:
            income_account = product_id.categ_id.property_account_income_categ_id.id
        else:
            raise UserError(_('Please define income '
                              'account for this product: "%s" (id:%d).')
                            % (product_id.name, product_id.id))
        for invoice in invoices:
            if invoice.property_id.allow_delay_fine:
                after2_days = invoice.property_id.delay_fine_id.after_days
                after2_date = invoice.invoice_date_due + timedelta(days=after2_days)
                if after2_date == fields.Date.today():
                    fine_percent = invoice.property_id.delay_fine_id.fine_on_property_price
                    fine_amount = invoice.property_id.discounted_price * fine_percent / 100
                    values = {
                        'narration': invoice.property_id.delay_fine_id.name,
                        'property_id': invoice.property_id.id,
                        'move_type': 'out_invoice',
                        'invoice_origin': invoice.property_id.name,
                        'partner_id': invoice.property_id.purchaser_id.id,
                        'invoice_date': fields.Date.today(),
                        'invoice_user_id': invoice.property_id.salesperson_id.id,
                        'invoice_line_ids': [(0, 0, {'name': invoice.property_id.name + '-' + 'Delay Fine Payment',
                                                     'product_id': invoice.property_id.id, 'account_id': income_account,
                                                     'price_unit': fine_amount})],
                    }
                    invoice_id = self.env["account.move"].create(values)

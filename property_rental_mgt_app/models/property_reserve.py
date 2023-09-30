# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta


class PropertyBook(models.TransientModel):
    _name = 'property.book'
    _description = "Reserve Rental Property"

    def _default_company(self):
        return self.env.user.company_id

    contract_id = fields.Many2one('contract.contract', string="Choose Contract", required=True,
                                  help="Default expired and renewal date get by start(from) date for one month contract.")
    property_id = fields.Many2one('product.product', required=True, domain=[('is_property', '=', True)])
    unit_id = fields.Many2one('property.unit', string="Unit")
    desc = fields.Text()
    rent_price = fields.Float()
    owner_id = fields.Many2one('res.partner', string="Property Owner")
    renter_id = fields.Many2one('res.partner', string="Property Renter")
    monthly_rent = fields.Float(string="Monthly Rent", required=True,digits=(16, 3), store=True)
    from_date = fields.Date(string="From Date", required=True)
    to_date = fields.Date(string="Expired Date", required=True,
                          help="Default expired date automatically set for one month after start date. ")
    renewal_date = fields.Date("Renew Date", required=True)
    state = fields.Selection([('avl', 'Available'), ('reserve', 'Reserve')], string="Status", default='avl')
    contract_month = fields.Integer("Contract Months",
                                    help="Rent Contract months calculate base selected contract(monthly/yearly) type.")
    deposite_amount = fields.Float()
    total_deposite = fields.Float("Total Rent")
    month = fields.Integer()
    discount_offer = fields.Float("Discount Offer (%)")
    offer_price = fields.Float("Offer Price")
    offer_name = fields.Char()
    payment_by_cheque = fields.Boolean(string="Payment by Cheque")
    number_of_cheques = fields.Integer(string="Number of Cheque")
    cheque_numbers = fields.Text(string="Cheque Numbers/References",
                                 help="Enter cheque numbers or references, one per line")
    journal_id = fields.Many2one('account.journal', string='Journal',
                                 domain="[('type', 'in', ('bank', 'cash')), ('company_id', '=', company_id)]")
    company_id = fields.Many2one('res.company', default=_default_company)
    cheque_reference_ids = fields.One2many(
        'property.book.cheque.reference', 'property_book_id', string="Cheque Reference"
    )
    is_tax_included = fields.Boolean(string="Is tax included")
    contract_fee = fields.Float(string='Contract Fee', digits=(16, 3), store=True)

    @api.constrains('contract_fee')
    def check_contract_fee(self):
        for record in self:
            if record.contract_fee <= 0:
                raise ValidationError("Contract Fee must be greater than zero.")

    @api.onchange('from_date', 'contract_id','is_tax_included')
    def check_contract_date(self):
        if self.contract_id:
            if self.contract_id.contract_type == 'monthly':
                self.contract_month = self.contract_id.month
            if self.contract_id.contract_type == 'yearly':
                self.contract_month = self.contract_id.year * 12
            if self.contract_id.contract_type == 'by_date':
                self.from_date = self.contract_id.start_date
                self.to_date = self.contract_id.end_date
                self.contract_month = self.contract_id.month
            self.deposite_amount = self.contract_month * self.monthly_rent
            self.total_deposite = self.deposite_amount
            if self.is_tax_included:
                self.total_deposite += self.total_deposite*(5/100)
            self.month = self.contract_month
            if self.total_deposite > 0 or self.discount_offer > 0:
                discount = self.discount_offer * self.total_deposite / 100
                self.offer_price = self.total_deposite - discount

        if self.contract_id and self.from_date:
            if self.contract_id.contract_type == 'monthly':
                self.to_date = self.from_date + relativedelta(months=self.contract_id.month)
            if self.contract_id.contract_type == 'yearly':
                self.to_date = self.from_date + relativedelta(years=self.contract_id.year)
            if self.contract_id.contract_type == 'by_date':
                self.from_date = self.contract_id.start_date
                self.to_date = self.contract_id.end_date

        if self.from_date and self.to_date:
            self.to_date -= timedelta(days=1)
            self.renewal_date = self.to_date
            if self.from_date >= self.to_date:
                raise Warning(_("Select valid contract expired date..!"))
            if self.from_date and self.renewal_date:
                if self.from_date > self.renewal_date:
                    raise Warning(_("Select valid contract renewal date..!"))

    # get rent Property details.
    @api.model
    def default_get(self, default_fields):
        res = super(PropertyBook, self).default_get(default_fields)
        ctx = self._context
        property_data = {
            'deposite_amount': ctx.get('monthly_rent'),
            'property_id': ctx.get('property_id'),
            'unit_id': ctx.get('unit_id'),
            'desc': ctx.get('desc'),
            'rent_price': ctx.get('rent_price'),
            'renter_id': ctx.get('renter_id'),
            'owner_id': ctx.get('owner_id'),
            'monthly_rent': ctx.get('monthly_rent'),
            'discount_offer': ctx.get('discount_offer'),
            'offer_name': ctx.get('offer_name')
        }
        res.update(property_data)
        return res

    @api.onchange('number_of_cheques', 'from_date', 'total_deposite')
    def onchange_number_of_cheques(self):
        if self.payment_by_cheque and self.number_of_cheques > 0 and self.from_date and self.total_deposite:
            self.cheque_reference_ids = [(5, 0, 0)]  # Clear existing lines
            cheque_lines_ids = []
            total_days = (self.to_date - self.from_date).days
            duration = total_days / self.number_of_cheques
            pdc_date = self.from_date
            for i in range(self.number_of_cheques):
                cheque_lines_ids.append((0, 0, {
                    'property_book_id': self.id,
                    'customer_id': self.renter_id.id,
                    'payment_date': pdc_date,
                    'payment_amount': self.total_deposite / self.number_of_cheques,
                }))
                pdc_date += timedelta(days=duration)

            if self._context.get('from_reserve_property'):
                # Create a deposit line and set Deposite to True
                deposit_line = (0, 0, {
                    'property_book_id': self.id,
                    'customer_id': self.renter_id.id,
                    'payment_date': fields.Date.today(),
                    'payment_amount': self.total_deposite * 5 / 100,
                    'is_deposit': True,
                })
                cheque_lines_ids.append(deposit_line)
            # if self.to_date:
            #     self.to_date -= timedelta(days=1)
            self.cheque_reference_ids = cheque_lines_ids

    def create_contract_invoice(self,difference, contract_id):
        journal_id = self.env['account.journal'].search([('type', '=', 'sale')], limit=1)
        line_vals = {
            'name': 'Contract value service fees',
            'quantity': 1,
            'price_unit': difference,
        }
        move_vals = {
            'date': self.from_date,
            'ref': self.property_id.name,
            'move_type': 'out_invoice',
            'journal_id': journal_id.id,
            'contract_id': contract_id.id,
            'currency_id': journal_id.currency_id.id or self.env.company.currency_id.id,
            'partner_id': self.renter_id.id,
            'invoice_line_ids': [(0, 0, line_vals)]
        }
        self.env['account.move'].create(move_vals)

    def create_deposit_journal_entry(self, journal_id, deposit_amount, renter_id, contract):
        company = self.env.company.sudo()
        deposit_account = company.deposit_account_id
        if not deposit_account:
            raise ValidationError("Please configure deposit in the company settings.")
        # Determine the journal type (bank or not) and adjust debit and credit accounts
        if journal_id.type == 'bank':
            line_ids = [
                (0, 0, {
                    'account_id': deposit_account.id,
                    'name': 'Deposit',
                    'credit': deposit_amount,
                }),
                (0, 0, {
                    'account_id': journal_id.default_account_id.id,
                    'name': 'Cash or Bank',
                    'debit': deposit_amount,
                }),
            ]
        else:
            line_ids = [
                (0, 0, {
                    'account_id': deposit_account.id,
                    'name': 'Deposit',
                    'debit': deposit_amount,
                }),
                (0, 0, {
                    'account_id': journal_id.default_account_id.id,
                    'name': 'Cash or Bank',
                    'credit': deposit_amount,
                }),
            ]

        # Create the journal entry
        move_vals = {
            'date': fields.Date.today(),
            'journal_id': journal_id.id,
            'partner_id': renter_id.id,
            'contract_id': contract.id,
            'property_id': contract.property_id.id,
            'unit_id': contract.unit_id.id,
            'is_deposit': True,
            'line_ids': line_ids,
        }
        move = self.env['account.move'].create(move_vals)
        return move

    def create_accrued_income_journal_entry(self, contract):
        debit_account = self.company_id.debit_account_id
        credit_account = self.company_id.credit_account_id
        if not debit_account or not credit_account:
            raise ValidationError("Please configure debit and credit accounts in the company settings.")
        contract_start_date = fields.Date.from_string(contract.from_date)
        reference_date = contract_start_date.replace(month=12, day=31)
        # Calculate the number of days accrued
        # days_accrued = (contract_start_date - reference_date).days
        days_accrued = (reference_date - contract_start_date).days
        contract_days = contract.contract_month * 365 / 12
        value_per_day = contract.deposite / contract_days
        # contract_start_date = fields.Date.from_string(contract.from_date)
        # reference_date = fields.Date.from_string("2022-12-31")  # Change this date to 31/12 of the relevant year
        # days_accrued = (contract_start_date - reference_date).days
        # contract_days = contract.contract_month * 365/12
        # value_per_day = contract.deposite / contract_days
        # Calculate the amount for the journal entry
        accrued_amount = value_per_day * days_accrued
        # Create the journal entry
        journal = self.env['account.journal'].search([('type', '=', 'sale')],
                                                     limit=1)
        if not journal:
            raise ValidationError("Please configure a sale journal for creating accrued income journal entries.")
        move_vals = {
            'date': fields.Date.today(),
            'journal_id': journal.id,
            'partner_id': contract.partner_id.id,
            'contract_id': contract.id,
            'property_id': contract.property_id.id,
            'unit_id': contract.unit_id.id,
            'is_accrued': True,
            'line_ids': [
                (0, 0, {
                    'account_id': debit_account.id,
                    'name': 'Accrued Income',
                    'debit': accrued_amount,
                }),
                (0, 0, {
                    'account_id': credit_account.id,
                    'name': 'Accrued Income',
                    'credit': accrued_amount,
                }),
            ],
        }
        move = self.env['account.move'].create(move_vals)
        return move

    def create_rent_contract(self):
        # if self.number_of_cheques > 0 and not self.cheque_numbers:
        #     raise ValidationError("Cheque Numbers/References are required !.")
        if self.payment_by_cheque and self.number_of_cheques == 0:
            raise ValidationError("Please input at least one cheque")
        if self.number_of_cheques > 0:
            if self._context.get('from_reserve_property'):
                if len(self.cheque_reference_ids)-1 != self.number_of_cheques:
                    raise ValidationError("Please input %s check reference !." % self.number_of_cheques)
            else:
                if len(self.cheque_reference_ids) != self.number_of_cheques:
                    raise ValidationError("Please input %s check reference !." % self.number_of_cheques)
        if self.number_of_cheques > 0 and len(self.cheque_reference_ids)-1 == self.number_of_cheques:
            # total_payment_amount = sum(cheque.payment_amount for cheque in self.cheque_reference_ids)
            total_payment_amount = sum(
                cheque.payment_amount for cheque in self.cheque_reference_ids if not cheque.is_deposit)
            if total_payment_amount != self.total_deposite:
                raise ValidationError(_("Total payment amount in cheque references doesn't match the rent price."))
        if self.renter_id:
            if self.renter_id.email:
                portal_group = self.env.ref('base.group_portal')
                existing_portal_user = self.renter_id.user_ids.filtered(
                    lambda user: user.has_group('base.group_portal'))
                if not existing_portal_user:
                    # raise ValidationError(_('The partner "%s" already has a portal user.' % self.renter_id.name))
                    user_values = {
                        'partner_id': self.renter_id.id,
                        'login': self.renter_id.email,  # email can be used as login
                        'name': self.renter_id.name,
                        'email': self.renter_id.email,
                        'groups_id': [(6, 0, [portal_group.id])]
                    }
                    portal_user = self.env['res.users'].create(user_values)
                    portal_user.action_reset_password()

            else:
                raise ValidationError(_("%s has no email id.") % self.renter_id.name)

        if self.deposite_amount > 0 and self.discount_offer > 0:
            discount = self.discount_offer * self.deposite_amount / 100
            self.offer_price = self.deposite_amount - discount
        if self.from_date <= fields.Date.today():
            state = 'running'
        else:
            state = 'new'

        # rent offer
        rent_amount = 0
        if self.offer_price and self.month > 0:
            rent_amount = self.offer_price
        else:
            if self.monthly_rent > 0 and self.month > 0:
                rent_amount = self.monthly_rent * self.month
        contract_id = self.env['contract.details'].sudo().create({
            'contract_month': self.month,
            'deposite': self.deposite_amount,
            'renewal_date': self.renewal_date,
            'rent_price': self.property_id.rent_price,
            'contract_id': self.contract_id.id,
            'owner_id': self.owner_id.id,
            'renewal_date': self.renewal_date,
            'partner_id': self.renter_id.id,
            'property_id': self.property_id.id,
            'unit_id': self.unit_id.id,
            'date': fields.Date.today(),
            'from_date': self.from_date,
            'to_date': self.to_date,
            'state': state,
            'offer_price': rent_amount,
            'discount_offer': self.discount_offer,
            'offer_name': self.offer_name,
            'number_of_cheques': self.number_of_cheques,
        })

        # Create a deposit journal entry
        if self.deposite_amount > 0:
            if self.payment_by_cheque and self.cheque_reference_ids:
                deposit_journal_ids = self.cheque_reference_ids.filtered(lambda r: r.is_deposit)
                if deposit_journal_ids:
                    deposit_journal_id = deposit_journal_ids[0].journal_id
                    deposit_journal_entry = self.create_deposit_journal_entry(
                        deposit_journal_id, self.deposite_amount * 5 / 100, self.renter_id, contract_id)
            # deposit_journal_entry = self.create_deposit_journal_entry(self.deposite_amount*5/100, self.renter_id,contract_id)
            accrued_income_journal_entry = self.create_accrued_income_journal_entry(contract_id)
        # Create an accrued income journal entry
        # if self.from_date <= fields.Date.today():
        #     accrued_income_journal_entry = self.create_accrued_income_journal_entry(contract_id)
        #     print(accrued_income_journal_entry,"333333333333333333333333333333333333333")
        if contract_id:
            self.property_id.write({'renter_history_ids': [(0, 0, {
                'contract_month': self.month,
                'deposite': self.deposite_amount,
                'reference': self.contract_id.name,
                'property_id': self.property_id.id,
                'unit_id': self.unit_id.id,
                'owner_id': self.owner_id.id,
                'state': self.state,
                'rent_price': self.rent_price,
                'renter_id': self.renter_id.id,
                'date': fields.Date.today(),
                'from_date': self.from_date,
                'to_date': self.to_date,
                'contract_id': contract_id.id,
                'offer_price': rent_amount,
                'discount_offer': self.discount_offer,
            })]})
            self.property_id.write({'state': 'reserve', 'is_reserved': True, 'user_id': self.env.user.id})
            self.unit_id.write({'state': 'reserve', 'is_reserved': True, 'user_id': self.env.user.id})
            template_id = self.env.ref('property_rental_mgt_app.property_reserved_template')
            values = template_id.generate_email(self.id,
                                                ['subject', 'body_html', 'email_from', 'email_to', 'partner_to',
                                                 'email_cc', 'reply_to', 'scheduled_date'])
            mail_mail_obj = self.env['mail.mail']
            msg_id = mail_mail_obj.sudo().create(values)
            if msg_id:
                mail_mail_obj.sudo().send(msg_id)
                if self.payment_by_cheque and self.cheque_reference_ids:
                    non_deposit_cheque_references = self.cheque_reference_ids.filtered(lambda r: not r.is_deposit)
                    payment_list = []
                    count = 1
                    # for cheque_number in self.cheque_reference_ids:
                    for cheque_number in non_deposit_cheque_references:
                        payment_method_lines = cheque_number.journal_id._get_available_payment_method_lines('outbound')
                        if payment_method_lines:
                            payment_method_id = payment_method_lines[0].payment_method_id.id
                        else:
                            payment_method_id = False
                        payment_vals = {
                            'partner_id': cheque_number.customer_id.id,
                            'amount': cheque_number.payment_amount,
                            'journal_id': cheque_number.journal_id.id,
                            'payment_type': 'inbound',
                            'partner_type': 'customer',
                            'is_pdc_payment': True,
                            'payment_method_id': payment_method_id,
                            # 'payment_method_id': cheque_number.journal_id._get_available_payment_method_lines('outbound')[0].payment_method_id.id,
                            'date': cheque_number.payment_date,
                            'cheque_date': cheque_number.payment_date,
                            'due_date': cheque_number.payment_date,
                            'reference': cheque_number.cheque_number, # Use individual cheque number as communication
                            'ref': str(count) + '/' + str(cheque_number.cheque_number)
                        }
                        payment_list.append(payment_vals)
                        count+=1
                    payments = self.env['account.payment'].create(payment_list)
                    contract_id.write({'payment_ids': [(6, 0, payments.ids)]})
                    # todo update below logic
                    # self.create_contract_invoice(contract_id)
                    company = self.env.company.sudo()
                    if self.contract_fee and company and self.contract_fee > company.contract_value:
                        difference = self.contract_fee - company.contract_value
                        additional_invoice = self.create_contract_invoice(difference, contract_id)

                return {
                    'name': 'Contract Details',
                    'type': 'ir.actions.act_window',
                    'view_mode': 'tree,form',
                    'res_id': contract_id.id,
                    'views': [(self.env.ref('property_rental_mgt_app.property_contract_details_form').id, 'form')],
                    'res_model': 'contract.details',
                    'domain': [('invoice_id', '=', self.property_id.id)],
                }


class PropertyBookChequeReference(models.TransientModel):
    _name = 'property.book.cheque.reference'
    _description = "Property Book Cheque Reference"

    def _default_company(self):
        return self.env.user.company_id

    property_book_id = fields.Many2one('property.book', string="Property Book")
    cheque_number = fields.Char(string="Cheque Numbers/References", help="Enter cheque numbers or references, one per line")
    payment_date = fields.Date('Payment Date')
    payment_amount = fields.Float(string='Payment Amount')
    customer_id = fields.Many2one('res.partner', string="Customer")
    journal_id = fields.Many2one('account.journal', string='Journal',
                                 domain="[('type', 'in', ('bank', 'cash')), ('company_id', '=', company_id)]")
    company_id = fields.Many2one('res.company', default=_default_company)
    is_deposit = fields.Boolean("Is Deposit", default=False)


# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class AccountPaymentRegister(models.TransientModel):
	_inherit = 'account.payment.register'


	reference = fields.Char("Cheque Reference")
	due_date = fields.Date("Cheque Due Date")
	cheque_date = fields.Date('Cheque Date', default=fields.Date.today())
	all_banks_ids = fields.Many2many('res.partner.bank', compute='compute_parnter_bank_ids')
	is_pdc_payment = fields.Boolean(string="Is PDC Payment", default=False)

	@api.depends('partner_id')
	def compute_parnter_bank_ids(self):
		all_banks_ids = []
		if self.partner_id:
			all_banks_ids = self.partner_id.bank_ids.ids
		self.all_banks_ids = all_banks_ids

	@api.onchange('journal_id')
	def onchange_journal_id(self):
		if self.journal_id and self.journal_id.is_pdc_journal:
			self.is_pdc_payment = True
		else:
			self.is_pdc_payment = False

	def _create_payments(self):
		res = super(AccountPaymentRegister,self)._create_payments()
		if self.is_pdc_payment:
			for rec in res:
				rec.write({
					'is_pdc_payment':self.is_pdc_payment,
					'reference':self.reference,
					'due_date':self.due_date,
					'cheque_date':self.cheque_date,
					'pdc_state':'registered'
					})
		return res

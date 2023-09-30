from odoo import api, fields, models
from odoo.exceptions import UserError

class accountJournal(models.Model):
    _inherit = 'account.journal'

    is_pdc_journal = fields.Boolean(string="Is PDC Journal", default=False)

class accountPayment(models.Model):
    _inherit = "account.payment"

    # This method is used to compute bank accounts related to a partner to be used as a domain for the 'Partner Bank' field 
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

    reference = fields.Char("Cheque Reference")
    due_date = fields.Date("Cheque Due Date")
    deposit_date = fields.Date('Deposit  Date')
    bounce_date = fields.Date('Bounce Date')
    cheque_date = fields.Date('Cheque Date', default=fields.Date.today())
    all_banks_ids = fields.Many2many('res.partner.bank', compute='compute_parnter_bank_ids')
    is_pdc_payment = fields.Boolean(string="Is PDC Payment", default=False)
    pdc_state = fields.Selection([
                            ('registered', 'Registered'),
                            ('settled', 'Settled'), 
                            ('bounced', 'Bounced'), 
                            ('deposited', 'Deposited'), 
                            ('cancel', 'Cancelled')], string="PDC State")

    def action_settle(self):
        self.pdc_state = 'settled'

    def action_deposit(self):
        return {
            'type':'ir.actions.act_window',
            'name':'Deposit Cheuqe',
            'res_model':'deposit.date.wizard',
            'view_mode':'form',
            'context':{'default_payment_id':self.id},
            'target':'new'
        }

    def action_bounce(self):
        for rec in self:
            if rec.is_pdc_payment:
                rec.pdc_state = 'bounced'

    def action_cancel(self):
        res = super(accountPayment,self).action_cancel()
        if self.is_pdc_payment:
            self.move_id.line_ids.remove_move_reconcile()
            self.pdc_state = 'cancel'
        return res

    def action_draft(self):
        res = super(accountPayment,self).action_draft()
        for rec in self:
            if rec.is_pdc_payment:
                rec.pdc_state = ''
        return res

    def action_post(self):
        res = super(accountPayment,self).action_post()
        for rec in self:
            if rec.is_pdc_payment:
                rec.pdc_state = 'registered'
        return res
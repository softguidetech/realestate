# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from dateutil import relativedelta
from datetime import date, datetime
from odoo.exceptions import UserError

class SaleOffer(models.Model):
    _name = 'sale.offer'
    _description = "Sale Offer"

    name = fields.Char(required=True)
    partner_id = fields.Many2one('res.partner', "Partner", domain=([('partner_type','in',('renter','purchaser'))]))
    duration_days = fields.Integer("Days")
    duration_month = fields.Integer("Month")
    start_date = fields.Date(required=True)
    end_date = fields.Date(required=True)
    offer_price = fields.Float()
    property_price = fields.Float()
    discount_offer = fields.Float("Discount Offer (%)", required=True)
    company_id = fields.Many2one('res.company', default=lambda self: self.env.user.company_id)
    user_id = fields.Many2one('res.users',default=lambda self: self.env.user)
    state = fields.Selection([('draft','Draft'),('open','Open'),('close','Close')], default='draft')
    note = fields.Text()

    def confirm_sale_offer(self):
        offer = self.search([('state','!=','close'),('id','!=',self.id)])
        flag = True
        for o in offer:
            if self.start_date >= o.start_date and self.start_date <= o.end_date:
                flag = False
                raise UserError(_("Defined Offer Start Date already exist, in existed Offer Date Range...!"))
            if self.end_date >= o.start_date and self.end_date <= o.end_date:
                flag = False
                raise UserError(_("Defined Offer End Date already exist, in existed Offer Date Range...!"))
            if self.start_date <= o.start_date and o.end_date <= self.end_date:
                flag = False
                raise UserError(_("Sale Offer already exist in Between Date Range..!"))
        
        if self.discount_offer <= 0.00:
            raise UserError(_("Please enter valid Discount Offer(%)..!"))
        
        if flag:
        	self.write({'state':'open'})

    @api.onchange('start_date','end_date')
    def _onchange_month_days(self):
        if self.start_date:
            if self.start_date < date.today():
                return {
                         'warning': {'title': 'Warning!', 'message': 'Please enter valid Start Date...!'},
                          'value': {'start_date': None}
                        }
        if self.end_date and self.start_date:
            if self.end_date < date.today() or self.end_date < self.start_date:
                return {
                         'warning': {'title': 'Warning!', 'message': 'Please enter valid End Date...!'},
                          'value': {'end_date': None}
                        }
        result = relativedelta.relativedelta(self.end_date, self.start_date)
        months = result.months + (12*result.years)
        self.duration_month = months
        self.duration_days = result.days


class PropertySaleOffer(models.Model):
    _name = 'property.sale.offer'
    _description = "Property Sale Offer"

    offer_id = fields.Many2one('sale.offer', domain=[('state','=','open')])
    name = fields.Char(required=True, related='offer_id.name')
    partner_id = fields.Many2one('res.partner', "Partner", domain=([('partner_type','in',('renter','purchaser'))]),related='offer_id.partner_id')
    property_id = fields.Many2one('product.product')
    duration_days = fields.Integer("Days",related='offer_id.duration_days')
    duration_month = fields.Integer("Month",related='offer_id.duration_month')
    start_date = fields.Date(required=True,related='offer_id.start_date')
    end_date = fields.Date(required=True,related='offer_id.end_date')
    offer_price = fields.Float()
    property_price = fields.Float()
    discount_offer = fields.Float("Discount Offer (%)", required=True,related='offer_id.discount_offer')
    company_id = fields.Many2one('res.company', default=lambda self: self.env.user.company_id)
    user_id = fields.Many2one('res.users',default=lambda self: self.env.user)
    state = fields.Selection(related='offer_id.state', string="State")
    note = fields.Text("Description",related='offer_id.note')

    @api.onchange('property_id', 'offer_id')
    def _onchange_property(self):
        if self.property_id:
            self.property_price = self.property_id.discounted_price
        if self.offer_id:
            if self.discount_offer > 0 and self.property_price > 0:
                discount  = (self.property_price * self.discount_offer)/100
                self.offer_price = self.property_price - discount

class RentOffer(models.Model):
    _name = 'rent.offer'
    _description = "Rent Offer"

    name = fields.Char(required=True)
    partner_id = fields.Many2one('res.partner', "Partner", domain=([('partner_type','in',('renter','purchaser'))]))
    # property_id = fields.Many2one('product.product', domain=[('is_property','=',True),('property_book_for','=','sale'),('state','!=','sold')],required=True)
    duration_days = fields.Integer("Days")
    duration_month = fields.Integer("Month")
    start_date = fields.Date(required=True)
    end_date = fields.Date(required=True)
    offer_price = fields.Float()
    property_price = fields.Float()
    discount_offer = fields.Float("Discount Offer (%)", required=True)
    company_id = fields.Many2one('res.company', default=lambda self: self.env.user.company_id)
    user_id = fields.Many2one('res.users',default=lambda self: self.env.user)
    state = fields.Selection([('draft','Draft'),('open','Open'),('close','Close')], default='draft')
    note = fields.Text()

    @api.onchange('start_date','end_date')
    def _onchange_month_days(self):
        if self.start_date:
            if self.start_date < date.today():
                return {
                         'warning': {'title': 'Warning!', 'message': 'Please enter valid Start Date...!'},
                          'value': {'start_date': None}
                        }
        if self.end_date and self.start_date:
            if self.end_date < date.today() or self.end_date < self.start_date:
                return {
                         'warning': {'title': 'Warning!', 'message': 'Please enter valid End Date...!'},
                          'value': {'end_date': None}
                        }
        result = relativedelta.relativedelta(self.end_date, self.start_date)
        months = result.months + (12*result.years)
        self.duration_month = months
        self.duration_days = result.days

    def confirm_rent_offer(self):
        offer = self.search([('state','!=','close'),('id','!=',self.id)])
        flag = True
        for o in offer:
            if self.start_date >= o.start_date and self.start_date <= o.end_date:
                flag = False
                raise UserError(_("Defined Offer Start Date already exist, in existed Offer Date Range...!"))
            if self.end_date >= o.start_date and self.end_date <= o.end_date:
                flag = False
                raise UserError(_("Defined Offer End Date already exist, in existed Offer Date Range...!"))
            if self.start_date <= o.start_date and o.end_date <= self.end_date:
                flag = False
                raise UserError(_("Rent Offer already exist in Between Date Range..!"))
        
        if self.discount_offer <= 0.00:
            raise UserError(_("Please enter valid Discount Offer(%)..!"))
        
        if flag:
        	self.write({'state':'open'})

class PropertyRentOffer(models.Model):
    _name = 'property.rent.offer'
    _description = "Property Rent Offer"

    offer_id = fields.Many2one('rent.offer', domain=[('state','=','open')])
    name = fields.Char(required=True, related='offer_id.name')
    partner_id = fields.Many2one('res.partner', "Partner", domain=([('partner_type','in',('renter','purchaser'))]),related='offer_id.partner_id')
    property_id = fields.Many2one('product.product')
    duration_days = fields.Integer("Days",related='offer_id.duration_days')
    duration_month = fields.Integer("Month",related='offer_id.duration_month')
    start_date = fields.Date(required=True,related='offer_id.start_date')
    end_date = fields.Date(required=True,related='offer_id.end_date')
    offer_price = fields.Float()
    property_price = fields.Float()
    discount_offer = fields.Float("Discount Offer (%)", required=True,related='offer_id.discount_offer')
    company_id = fields.Many2one('res.company', default=lambda self: self.env.user.company_id)
    user_id = fields.Many2one('res.users',default=lambda self: self.env.user)
    state = fields.Selection(related='offer_id.state', string="State")
    note = fields.Text("Description",related='offer_id.note')

    @api.onchange('property_id','offer_id')
    def _onchange_property(self):
        if self.property_id:
            self.property_price = self.property_id.deposite
        if self.offer_id:
            if self.discount_offer > 0 and self.property_price > 0:
                discount  = (self.property_price * self.discount_offer)/100
                self.offer_price = self.property_price - discount

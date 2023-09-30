# -*- coding: utf-8 -*-

from odoo import models, fields, api, _

class PropertyList(models.Model):
    _name = 'property.list'
    _description = "Property List"

    name = fields.Char(required=True)
    property_id = fields.Many2one('product.product', domain=[('is_property','=',True)])
    property_search_id = fields.Many2one('property.search')
    price = fields.Float("Price")
    property_type_id = fields.Many2one('property.type')
    city = fields.Char()
    state_id = fields.Many2one('res.country.state')
    country_id = fields.Many2one('res.country')
    salesperson_id = fields.Many2one('res.users')
    owner_id = fields.Many2one('res.partner')
    property_for = fields.Char()
    state = fields.Selection([('draft','Draft'),('rent','Rentable'),('sale','Saleable'),('reserve','Reserve'),('sold','Sold')], string="Status", help='State of the Property',default='draft')
    company_id = fields.Many2one('res.company', default=lambda self: self.env.user.company_id)

    def view_searched_property(self):
        action = self.env.ref('property_rental_mgt_app.property_product_action').read()[0]
        if len(self.property_id) > 1:
            action['domain'] = [('id', '=', self.property_id.id)]
        if len(self.property_id) == 1:
            action['views'] = [(self.env.ref('product.product_normal_form_view').id, 'form')]
            action['res_id'] = self.property_id.ids[0]
        else:
            action = {'type': 'ir.actions.act_window_close'}
        return action

class PropertySearch(models.Model):
    _name = 'property.search'
    _description = "Property Search"

    name = fields.Char()
    company_id = fields.Many2one('res.company', required=True, default=lambda self: self.env.user.company_id)
    user_id = fields.Many2one('res.users',default=lambda self: self.env.user)
    property_list_ids = fields.One2many('property.list','property_search_id')
    price_start = fields.Float("Price Range", default=1)
    price_end = fields.Float(default=100000)
    filter_by = fields.Selection([('sale', 'Available Sale Property'),('rent','Available Rent Property'),('all','All Properties')], default='sale', string="Filter By Type")
    property_type_id = fields.Many2one('property.type', string="Category")

    def clear(self):
        self.name = ''
        self.price_start = 0
        self.price_end = 0
        self.filter_by = 'all'
        self.property_type_id = False
        self.property_list_ids.unlink()

    def search_property(self):
        self.property_list_ids.unlink()
        if self.filter_by == 'sale':
            p_sale = self.env['product.product'].search([('property_book_for','=', self.filter_by),('is_property','=',True),('state','!=','sold')])
            if self.name:
                p_sale = self.env['product.product'].search([('name','ilike', self.name),('property_book_for','=', self.filter_by),('is_property','=',True),('state','!=','sold')])
            if self.property_type_id:
                p_sale = self.env['product.product'].search([('property_book_for','=', self.filter_by),('property_type','=', self.property_type_id.id),('is_property','=',True),('state','!=','sold')])
            if self.price_start > 0 and self.price_end > 0:
                p_sale = self.env['product.product'].search([('discounted_price','>=', self.price_start), ('discounted_price','<=', self.price_end),('property_book_for','=', self.filter_by),('is_property','=',True),('state','!=','sold')])
            if self.property_type_id and self.name:
                p_sale = self.env['product.product'].search([('property_book_for','=', self.filter_by),('property_type','=', self.property_type_id.id),('name','ilike', self.name),('is_property','=',True),('state','!=','sold')])
            if self.property_type_id and self.price_start > 0 and self.price_end > 0:
                p_sale = self.env['product.product'].search([('discounted_price','>=', self.price_start), ('discounted_price','<=', self.price_end),('property_book_for','=', self.filter_by),('property_type','=',self.property_type_id.id),('is_property','=',True),('state','!=','sold')])
            if self.name and self.price_start > 0 and self.price_end > 0:
                p_sale = self.env['product.product'].search([('discounted_price','>=', self.price_start), ('discounted_price','<=', self.price_end),('property_book_for','=', self.filter_by),('name','ilike', self.name),('is_property','=',True),('state','!=','sold')])
            if self.property_type_id and self.name and self.price_start > 0 and self.price_end > 0:
                p_sale = self.env['product.product'].search([('discounted_price','>=', self.price_start), ('discounted_price','<=', self.price_end),('property_book_for','=', self.filter_by),('name','ilike', self.name),('property_type','=',self.property_type_id.id),('is_property','=',True),('state','!=','sold')])
            for p in p_sale: 
                self.env['property.list'].create({'name': p.name,'state':p.state,'property_for':p.property_book_for,'city':p.city,'state_id':p.state_id.id,'country_id':p.country_id.id,'property_type_id':p.property_type.id,'property_id':p.id,'property_search_id':self.id,'price':p.discounted_price, 'salesperson_id':p.salesperson_id.id,'owner_id':p.owner_id.id})

        if self.filter_by == 'rent':
            p_rent = self.env['product.product'].search([('property_book_for','=', self.filter_by),('is_property','=',True),('state','!=','reserve')])
            if self.name:
                p_rent = self.env['product.product'].search([('property_book_for','=', self.filter_by),('name','ilike', self.name),('is_property','=',True),('state','!=','reserve')])
            if self.property_type_id:
                p_rent = self.env['product.product'].search([('property_book_for','=', self.filter_by),('property_type','=', self.property_type_id.id),('is_property','=',True),('state','!=','reserve')])
            if self.price_start > 0 and self.price_end > 0:
                p_rent = self.env['product.product'].search([('deposite','>=', self.price_start), ('deposite','<=', self.price_end),('property_book_for','=', self.filter_by),('is_property','=',True),('state','!=','reserve')])
            if self.property_type_id and self.name:
                p_rent = self.env['product.product'].search([('property_book_for','=', self.filter_by),('property_type','=', self.property_type_id.id),('name','ilike', self.name),('is_property','=',True)])
            if self.property_type_id and self.price_start > 0 and self.price_end > 0:
                p_rent = self.env['product.product'].search([('deposite','>=', self.price_start), ('deposite','<=', self.price_end),('property_book_for','=', self.filter_by),('property_type','=',self.property_type_id.id),('is_property','=',True),('state','!=','reserve')])
            if self.name and self.price_start > 0 and self.price_end > 0:
                p_rent = self.env['product.product'].search([('deposite','>=', self.price_start),('deposite','<=', self.price_end),('property_book_for','=', self.filter_by),('name','ilike', self.name),('is_property','=',True),('state','!=','reserve')])
            if self.name and self.property_type_id and self.price_start > 0 and self.price_end > 0:
                p_rent = self.env['product.product'].search([('deposite','>=', self.price_start),('property_book_for','=', self.filter_by),('name','ilike', self.name),('property_type','=', self.property_type_id.id),('is_property','=',True),('state','!=','reserve')])
            for p in p_rent:
                self.env['property.list'].create({'name': p.name,'state':p.state,'property_for':p.property_book_for,'city':p.city,'state_id':p.state_id.id,'country_id':p.country_id.id,'property_type_id':p.property_type.id,'property_id':p.id,'property_search_id':self.id,'price':p.deposite,'salesperson_id':p.salesperson_id.id,'owner_id':p.owner_id.id})
 
        if self.filter_by == 'all':
            p_all = self.env['product.product'].search([('is_property','=', True),('is_property','=',True)])
            if self.name:
                p_all = self.env['product.product'].search([('name','ilike', self.name),('is_property','=',True)])
            if self.property_type_id:
                p_all = self.env['product.product'].search([('property_type','=', self.property_type_id.id),('is_property','=',True)])
            if self.price_start > 0 and self.price_end > 0:
                rent = self.env['product.product'].search([('deposite','>=', self.price_start), ('deposite','<=', self.price_end),('is_property','=',True)])
                sale = self.env['product.product'].search([('discounted_price','>=', self.price_start), ('discounted_price','<=', self.price_end),('is_property','=',True)])
                p_all = rent + sale
            if self.property_type_id and self.price_start > 0 and self.price_end > 0:
                rent = self.env['product.product'].search([('deposite','>=', self.price_start), ('deposite','<=', self.price_end),('property_type','=',self.property_type_id.id),('is_property','=',True)])
                sale = self.env['product.product'].search([('discounted_price','>=', self.price_start), ('discounted_price','<=', self.price_end),('property_type','=',self.property_type_id.id),('is_property','=',True)])
                p_all = rent + sale
            if self.property_type_id and self.name:
                p_all = self.env['product.product'].search([('property_type','=', self.property_type_id.id),('name','ilike', self.name),('is_property','=',True)])
            if self.name and self.price_start > 0 and self.price_end > 0:
                rent = self.env['product.product'].search([('deposite','>=', self.price_start), ('deposite','<=', self.price_end),('name','ilike', self.name),('is_property','=',True)])
                sale = self.env['product.product'].search([('discounted_price','>=', self.price_start), ('discounted_price','<=', self.price_end),('name','ilike', self.name),('is_property','=',True)])
                p_all = rent + sale
            if self.property_type_id and self.name and self.price_start > 0 and self.price_end > 0:
                rent = self.env['product.product'].search([('deposite','>=', self.price_start), ('deposite','<=', self.price_end),('name','ilike', self.name),('property_type','=',self.property_type_id.id),('is_property','=',True)])
                sale = self.env['product.product'].search([('discounted_price','>=', self.price_start), ('discounted_price','<=', self.price_end),('name','ilike', self.name),('property_type','=',self.property_type_id.id),('is_property','=',True)])
                p_all = rent + sale

            for p in p_all: 
                if p.property_book_for == 'sale':
                    price = p.discounted_price
                else:
                    price = p.deposite 
                self.env['property.list'].create({'name': p.name,'state':p.state,'property_for':p.property_book_for,'city':p.city,'state_id':p.state_id.id,'country_id':p.country_id.id,'property_type_id':p.property_type.id,'property_id':p.id,'property_search_id':self.id,'price':price,'salesperson_id':p.salesperson_id.id,'owner_id':p.owner_id.id})
 
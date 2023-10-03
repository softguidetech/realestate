# -*- coding: utf-8 -*-

from odoo import models, fields, api, _

class UnitList(models.Model):
    _name = 'unit.list'
    _description = "unit List"

    unit_search_id = fields.Many2one('unit.search')
    name = fields.Char(string='Unit Ref', )
    code = fields.Char(string='Unit Code', )
    note = fields.Char(string='Note', )
    company_id = fields.Many2one('res.company')
    floor_id = fields.Many2one('property.floor', string='Floor')
    property_id = fields.Many2one('product.product', string='Property', domain=[('is_property', '=', True)])
    unit_area_feet = fields.Float(string='Unit Area feet', )
    unit_area_meter = fields.Float(string='Unit Area meter', )
    unit_id = fields.Many2one('property.unit', string='Unit')
    state = fields.Selection([('available', 'Available'), ('un_available', 'Un Available')], string="Availablitu Status")
    # state = fields.Selection(
    #     [('draft', 'Draft'), ('rent', 'Rentable'), ('sale', 'Saleable'), ('reserve', 'Reserve'), ('sold', 'Sold'),
    #      ('cancel', 'Cancelled')], default='draft', string="Property Status", help='State of the Property')
    deposit = fields.Float("Deposit")

    def view_searched_unit(self):
        action = self.env.ref('realestate_sgt.property_unit_action').sudo().read()[0]
        if len(self.unit_id) > 1:
            action['domain'] = [('id', '=', self.unit_id.id)]
        if len(self.unit_id) == 1:
            action['views'] = [(self.env.ref('realestate_sgt.property_unit_form').id, 'form')]
            action['res_id'] = self.unit_id.ids[0]
        else:
            action = {'type': 'ir.actions.act_window_close'}
        return action

class UnitSearch(models.Model):
    _name = 'unit.search'
    _description = "Unit Search"

    property_id = fields.Many2one('product.product', string="Property")
    state = fields.Selection([('available','Available'),('un_available','Un Available')], string="Availablitu Status", help='State of the Property')
    price_start = fields.Float("Price Range", default=1)
    price_end = fields.Float(default=100000)
    area_size_meter_start = fields.Float(string='Unit Area meter Start', )
    area_size_meter_end = fields.Float(string='Unit Area meter End', )
    unit_list_ids = fields.One2many('unit.list', 'unit_search_id')

    def clear(self):
        self.price_start = 0
        self.price_end = 0
        self.area_size_meter_start = 0
        self.area_size_meter_end = 0
        self.state = 'available'
        self.property_id = False
        self.unit_list_ids.unlink()

    def search_unit(self):
        self.unit_list_ids.unlink()  # Clear existing records
        domain = []
        unit_list = []
        if self.property_id:
            domain.append(('property_id', '=', self.property_id.id))
        if self.state:
            if self.state == 'available':
                domain.extend([
                    ('state', '=', 'rent')
                ])
            elif self.state == 'un_available':
                domain.extend([
                    ('state', '!=', 'rent')
                ])
        if self.price_start > 0 and self.price_end > 0:
            domain.extend([('deposit', '>=', self.price_start), ('deposit', '<=', self.price_end)])
        if self.area_size_meter_start > 0 and self.area_size_meter_end > 0:
            domain.extend([('unit_area_meter', '>=', self.area_size_meter_start), ('unit_area_meter', '<=', self.area_size_meter_end)])
        units = self.env['property.unit'].search(domain)
        for unit in units:
            state = 'available' if unit.state == 'rent' else 'un_available'
            unit_vals = {
                'unit_id': unit.id,
                'name': unit.name,
                'code': unit.code,
                'company_id': unit.company_id.id,
                'property_id': unit.property_id.id,
                'floor_id': unit.floor_id.id,
                'unit_area_feet': unit.unit_area_feet,
                'unit_area_meter': unit.unit_area_meter,
                'state': state,
                'deposit': unit.deposit,
            }
            unit_list.append(unit_vals)
        if unit_list:
            units_recs = self.env['unit.list'].create(unit_list)
            self.write({'unit_list_ids': [(6, 0, units_recs.ids)]})

    # def search_unit(self):
    #     self.property_list_ids.unlink()
    #
    #     domain = []
    #
    #     if self.unit_id:
    #         # Use a domain filter to check if any of the unit_ids contains the selected unit_id
    #         domain.append(('unit_ids', '=', self.unit_id.id))
    #
    #     if self.filter_by == 'sale':
    #         domain.extend([
    #             ('property_book_for', '=', self.filter_by),
    #             ('is_property', '=', True),
    #             ('state', '!=', 'sold')
    #         ])
    #     elif self.filter_by == 'rent':
    #         domain.extend([
    #             ('property_book_for', '=', self.filter_by),
    #             ('is_property', '=', True),
    #             ('state', '!=', 'reserve')
    #         ])
    #     elif self.filter_by == 'all':
    #         domain.extend([
    #             ('is_property', '=', True)
    #         ])
    #
    #     if self.name:
    #         domain.append(('name', 'ilike', self.name))
    #
    #     if self.property_type_id:
    #         domain.append(('property_type', '=', self.property_type_id.id))
    #
        # if self.price_start > 0 and self.price_end > 0:
        #     rent_domain = [('deposite', '>=', self.price_start), ('deposite', '<=', self.price_end)]
    #         sale_domain = [('discounted_price', '>=', self.price_start), ('discounted_price', '<=', self.price_end)]
    #
    #         if self.filter_by == 'sale':
    #             domain.extend(sale_domain)
    #         elif self.filter_by == 'rent':
    #             domain.extend(rent_domain)
    #         elif self.filter_by == 'all':
    #             domain.extend(rent_domain + sale_domain)
    #
    #     # Add condition to filter by availability status
    #     if self.state == 'available':
    #         domain.append(('unit_ids.state', '=', 'rent'))
    #     elif self.state == 'un_available':
    #         domain.append(('unit_ids.state', '!=', 'rent'))
    #
    #     properties = self.env['product.product'].search(domain)
    #
    #     for property in properties:
    #         if property.property_book_for == 'sale':
    #             price = property.discounted_price
    #         else:
    #             price = property.deposite
    #
    #         self.env['property.list'].create({
    #             'name': property.name,
    #             'state': property.state,
    #             'property_for': property.property_book_for,
    #             'city': property.city,
    #             'state_id': property.state_id.id,
    #             'country_id': property.country_id.id,
    #             'property_type_id': property.property_type.id,
    #             'property_id': property.id,
    #             'property_search_id': self.id,
    #             'price': price,
    #             'salesperson_id': property.salesperson_id.id,
    #             'owner_id': property.owner_id.id,
    #         })

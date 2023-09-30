# -*- coding: utf-8 -*-

from odoo import models, fields, api, _

class PropertyDocument(models.Model):
    _name = 'property.document'
    _description = "Property Document"

    name = fields.Char(required=True)
    user_id = fields.Many2one('res.users', default=lambda self: self.env.user)
    company_id = fields.Many2one('res.company', default=lambda self: self.env.user.company_id)
    file = fields.Binary(required=True)
    property_id = fields.Many2one('product.product', "Source Document")

class PropertyImages(models.Model):
    _name = 'property.image'
    _description = "Property Image"

    name = fields.Char(required=True)
    user_id = fields.Many2one('res.users', default=lambda self: self.env.user)
    company_id = fields.Many2one('res.company', default=lambda self: self.env.user.company_id)
    file = fields.Binary(required=True)
    property_id = fields.Many2one('product.product', "Source Document")


#
class UnitDocument(models.Model):
    _name = 'unit.document'
    _description = "Unit Document"

    name = fields.Char(required=True)
    user_id = fields.Many2one('res.users', default=lambda self: self.env.user)
    company_id = fields.Many2one('res.company', default=lambda self: self.env.user.company_id)
    file = fields.Binary(required=True)
    unit_id = fields.Many2one('property.unit', "Source Document")

class UnitImages(models.Model):
    _name = 'unit.image'
    _description = "Unit Image"

    name = fields.Char(required=True)
    user_id = fields.Many2one('res.users', default=lambda self: self.env.user)
    company_id = fields.Many2one('res.company', default=lambda self: self.env.user.company_id)
    file = fields.Binary(required=True)
    unit_id = fields.Many2one('property.unit', "Source Document")

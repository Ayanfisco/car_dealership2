from odoo import models, fields, api
from datetime import date


class CarFeature(models.Model):
    _name = 'car.dealership.feature'
    _description = 'Car Features'
    _order = 'name'

    name = fields.Char('Feature Name', required=True)
    category = fields.Selection([
        ('interior', 'Interior'),
        ('exterior', 'Exterior'),
        ('safety', 'Safety'),
        ('technology', 'Technology'),
        ('performance', 'Performance'),
    ], string='Category')
    active = fields.Boolean('Active', default=True)
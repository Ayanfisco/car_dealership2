from odoo import models, fields, api
from datetime import date

class CarMake(models.Model):
    _name = 'car.dealership.make'
    _description = 'Car Make/Brand'
    _order = 'name'

    name = fields.Char('Make Name', required=True)
    country = fields.Char('Country of Origin')
    logo = fields.Binary('Logo')
    active = fields.Boolean('Active', default=True)
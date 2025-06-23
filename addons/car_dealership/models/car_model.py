from odoo import models, fields, api
from datetime import date

class CarModel(models.Model):
    _name = 'car.dealership.model'
    _description = 'Car Model'
    _order = 'make_id, name'

    name = fields.Char('Model Name', required=True)
    make_id = fields.Many2one('car.dealership.make', string='Make', required=True)
    body_type = fields.Selection([
        ('sedan', 'Sedan'),
        ('suv', 'SUV'),
        ('hatchback', 'Hatchback'),
        ('coupe', 'Coupe'),
        ('convertible', 'Convertible'),
        ('wagon', 'Wagon'),
        ('truck', 'Truck'),
        ('van', 'Van'),
    ], string='Body Type')
    active = fields.Boolean('Active', default=True)
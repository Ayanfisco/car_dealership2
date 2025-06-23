from odoo import models, fields, api
from datetime import date


class CarImage(models.Model):
    _name = 'car.dealership.image'
    _description = 'Car Images'

    name = fields.Char('Description')
    image = fields.Binary('Image', required=True)
    car_id = fields.Many2one('car.dealership.car', string='Car', required=True, ondelete='cascade')
    sequence = fields.Integer('Sequence', default=10)
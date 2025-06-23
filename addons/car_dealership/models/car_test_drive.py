from odoo import fields, models

class TestDrive(models.Model):
    _name = 'car.dealership.test_drive'
    _description = 'Test Drive Request'

    car_id = fields.Many2one('car.dealership.car', string='Car', required=True, ondelete='restrict')
    name = fields.Char(string='Name', required=True)
    email = fields.Char(string='Email', required=True)
    date = fields.Date(string='Preferred Date', required=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('cancelled', 'Cancelled'),
    ], string='Status', default='draft', required=True)
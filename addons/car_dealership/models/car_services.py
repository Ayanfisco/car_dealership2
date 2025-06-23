from odoo import models, fields, api

class CarService(models.Model):
    _name = 'car.dealership.service'
    _description = 'Car Service History'
    _order = 'service_date desc'

    car_id = fields.Many2one('car.dealership.car', string='Car', required=True, ondelete='cascade')
    service_date = fields.Date('Service Date', required=True)
    service_type = fields.Char('Service Type', required=True)
    cost = fields.Monetary('Cost')
    currency_id = fields.Many2one('res.currency', string='Currency', default=lambda self: self.env.company.currency_id)
    description = fields.Text('Description')
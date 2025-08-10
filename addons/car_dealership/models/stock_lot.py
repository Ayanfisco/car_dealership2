from odoo import models, fields, api, _


class CarStockLot(models.Model):
    _inherit = 'stock.lot'

    name = fields.Char(string='VIN/Chassis Number', required=True)

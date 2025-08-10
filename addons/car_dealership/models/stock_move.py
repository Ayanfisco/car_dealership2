from odoo import fields, models, api, _


class StockMoveLine(models.Model):
    _inherit = 'stock.move.line'

    lot_id = fields.Many2one(
        'stock.production.lot',
        string='VIN/Chassis Number',  # Your custom label
        check_company=True,
    )

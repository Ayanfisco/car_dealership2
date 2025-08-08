from odoo import fields, models, api, _


class StockMoveLine(models.Model):
    _inherit = 'stock.move.line'

    # Override the field completely
    lot_name = fields.Char(
        string='VIN Number/Chasis Number',
        store=True,
        readonly=True,
        help="Vehicle Identification Number or Chassis Number"
    )

    # If the above doesn't work, try modifying the existing field
    def _setup_fields(self):
        super()._setup_fields()
        self._fields['lot_name'].string = 'VIN Number/Chasis Number'
        self._fields['lot_name'].readonly = True
        self._fields['lot_name'].store = True

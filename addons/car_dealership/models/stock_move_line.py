from odoo import models, fields, api

class StockMoveLine(models.Model):
    _inherit = 'stock.move.line'
    
    def write(self, vals):
        res = super().write(vals)
        # Auto-create fleet vehicles when stock is received
        if vals.get('state') == 'done':
            for line in self:
                if (line.product_id.is_vehicle and 
                    line.lot_id and 
                    line.location_dest_id.usage == 'internal'):
                    line.product_id.product_tmpl_id._auto_create_fleet_from_receipt(line)
        return res
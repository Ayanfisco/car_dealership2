from odoo import models, api

class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    @api.model
    def create(self, vals):
        line = super().create(vals)
        product = line.product_id.product_tmpl_id
        if product.is_vehicle:
            # Find or create dealership.vehicle record
            dealership_vehicle = line.env['dealership.vehicle'].search([
                ('make_id', '=', product.vehicle_make_id.id),
                ('model_id', '=', product.vehicle_model_id.id),
                ('year', '=', getattr(product, 'year', False)),
                ('color', '=', getattr(line.product_id, 'color', False)),
            ], limit=1)
            qty = line.product_qty
            if dealership_vehicle:
                dealership_vehicle.quantity += qty
            else:
                line.env['dealership.vehicle'].create({
                    'name': product.name,
                    'make_id': product.vehicle_make_id.id,
                    'model_id': product.vehicle_model_id.id,
                    'year': getattr(product, 'year', False),
                    'color': getattr(line.product_id, 'color', False),
                    'quantity': qty,
                })
        return line

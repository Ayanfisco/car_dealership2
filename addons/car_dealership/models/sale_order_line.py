from odoo import api, fields, models


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    vehicle_id = fields.Many2one(
        'dealership.vehicle',
        string='Vehicle',
        domain=[('state', '=', 'available')]
    )
    is_vehicle_product = fields.Boolean('Is Vehicle Product', default=False)

    @api.onchange('vehicle_id')
    def _onchange_vehicle_id(self):
        """When a vehicle is selected, populate the line with vehicle data"""
        if self.vehicle_id:
            self.product_id = False  # Clear product selection
            self.name = self.vehicle_id.name
            self.price_unit = self.vehicle_id.selling_price or 0.0
            self.product_uom_qty = 1
            self.is_vehicle_product = True
            # Set a default UOM (you might want to create a specific UOM for vehicles)
            self.product_uom = self.env.ref('uom.product_uom_unit').id

    @api.onchange('product_id')
    def _onchange_product_id(self):
        """When a regular product is selected, clear vehicle data"""
        if self.product_id:
            self.vehicle_id = False
            self.is_vehicle_product = False
        # Call the original product onchange logic
        # Note: we don't call super() here since the method doesn't exist
        # Instead, let the standard product onchange handle this

    @api.model_create_multi
    def create(self, vals_list):
        """Override create to handle vehicle-based lines"""
        for vals in vals_list:
            if vals.get('vehicle_id') and not vals.get('product_id'):
                vehicle = self.env['dealership.vehicle'].browse(
                    vals['vehicle_id'])
                if vehicle:
                    vals.update({
                        'name': vehicle.name,
                        'price_unit': vehicle.selling_price or 0.0,
                        'product_uom_qty': vals.get('product_uom_qty', 1),
                        'is_vehicle_product': True,
                        'product_uom': self.env.ref('uom.product_uom_unit').id,
                    })
        return super().create(vals_list)

    def write(self, vals):
        """Override write to handle vehicle updates"""
        if 'vehicle_id' in vals and vals['vehicle_id']:
            vehicle = self.env['dealership.vehicle'].browse(vals['vehicle_id'])
            if vehicle:
                vals.update({
                    'name': vehicle.name,
                    'price_unit': vehicle.selling_price or 0.0,
                    'is_vehicle_product': True,
                    'product_id': False,  # Clear product when vehicle is set
                })
        elif 'product_id' in vals and vals['product_id']:
            vals.update({
                'vehicle_id': False,  # Clear vehicle when product is set
                'is_vehicle_product': False,
            })
        return super().write(vals)

    def _prepare_invoice_line(self, **optional_values):
        """Ensure invoice line creation works with vehicles"""
        res = super()._prepare_invoice_line(**optional_values)
        if self.vehicle_id and self.is_vehicle_product:
            res.update({
                'name': self.vehicle_id.name,
                'price_unit': self.price_unit,
            })
        return res

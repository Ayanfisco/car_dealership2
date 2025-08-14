from odoo import models, fields, api, _


class ProductProduct(models.Model):
    _inherit = 'product.product'

    @api.model
    def search(self, args, offset=0, limit=None, order=None, count=False):
        """Override search to include vehicles when called from sale order lines"""
        # Check if this search is coming from a sale order line context
        if self.env.context.get('from_sale_order_line'):
            # Get regular products - REMOVE count parameter from super() call
            if count:
                # Handle count separately
                product_count = super().search_count(args)
                vehicle_count = self.env['dealership.vehicle'].search_count([
                    ('is_template_dummy', '=', False)
                ])
                return product_count + vehicle_count

            # Get products normally
            products = super().search(args, offset=offset, limit=limit, order=order)

            # Get vehicles and create "fake" product records for display
            vehicles = self.env['dealership.vehicle'].search([
                ('is_template_dummy', '=', False)
            ])

            # Create temporary product-like records for vehicles
            vehicle_products = self.env['product.product']
            for vehicle in vehicles:
                # Create a temporary product record that acts like the vehicle
                temp_product = self.env['product.product'].new({
                    'id': vehicle.id + 10000000,  # Offset ID to avoid conflicts
                    'name': f"🚗 {vehicle.name}",
                    'list_price': vehicle.selling_price or 0.0,
                    '_vehicle_id': vehicle.id,  # Store reference to actual vehicle
                })
                vehicle_products += temp_product

            return products + vehicle_products

        # For regular calls, use the standard search
        if count:
            return super().search_count(args)
        return super().search(args, offset=offset, limit=limit, order=order)

    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100):
        """Override name search to include vehicles"""
        if self.env.context.get('from_sale_order_line'):
            # Get regular product results
            product_results = super().name_search(name, args, operator, limit)

            # Search vehicles
            vehicle_domain = [
                ('is_template_dummy', '=', False),
                ('name', operator, name)
            ]
            vehicles = self.env['dealership.vehicle'].search(
                vehicle_domain, limit=limit)

            # Add vehicle results with offset IDs
            vehicle_results = [
                (vehicle.id + 10000000, f"🚗 {vehicle.name}")
                for vehicle in vehicles
            ]

            return product_results + vehicle_results

        return super().name_search(name, args, operator, limit)

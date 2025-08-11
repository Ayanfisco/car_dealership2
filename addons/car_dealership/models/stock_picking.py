from odoo import models, api
import logging

_logger = logging.getLogger(__name__)


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    def create_dealership_vehicles_from_receipt(self):
        """Create dealership vehicles from validated receipts"""
        for picking in self:
            if picking.picking_type_id.code == 'incoming' and picking.state == 'done':
                _logger.info(
                    f"Processing picking {picking.name} with {len(picking.move_line_ids)} move lines")

                for move_line in picking.move_line_ids:
                    product = move_line.product_id
                    lot = move_line.lot_id  # this is the VIN

                    _logger.info(
                        f"Processing move line - Product: {product.name if product else 'None'}, Lot: {lot.name if lot else 'None'}")

                    if product and lot and move_line.qty_done > 0:
                        # Check if dealership vehicle already exists
                        exists = self.env['dealership.vehicle'].search(
                            [('vin_number', '=', lot.name)], limit=1)

                        if not exists:
                            # Prepare vehicle data
                            vehicle_vals = {
                                'product_id': product.id,
                                'name': product.name,
                                'vin_number': lot.name,
                                'is_template_dummy': False,
                                'state': 'available',
                                'model_id': product.model_id.id if product.model_id else False,
                                'make_id': product.make_id.id if product.make_id else False,
                                'year': product.year if product.year else False,
                                'quantity': 1,  # Each serial number = 1 vehicle
                            }

                            # Add other product attributes if they exist
                            product_attrs = {
                                'color': 'vehicle_color',
                                'fuel_type': 'fuel_type',
                                'transmission': 'transmission',
                                'condition': 'condition',
                                'engine_size': 'engine_size',
                            }

                            for vehicle_field, product_field in product_attrs.items():
                                if hasattr(product, product_field):
                                    value = getattr(
                                        product, product_field, None)
                                    if value:
                                        vehicle_vals[vehicle_field] = value

                            # Add pricing information
                            if product.standard_price:
                                vehicle_vals['purchase_price'] = product.standard_price
                            if product.list_price:
                                vehicle_vals['selling_price'] = product.list_price

                            # Add commission information if available
                            commission_attrs = {
                                'commission_type': 'default_commission_type',
                                'commission_value': 'default_commission_value',
                                'vendor_id': 'default_vendor_id',
                            }

                            for vehicle_field, product_field in commission_attrs.items():
                                if hasattr(product, product_field):
                                    value = getattr(
                                        product, product_field, None)
                                    if value:
                                        vehicle_vals[vehicle_field] = value.id if hasattr(
                                            value, 'id') else value

                            _logger.info(
                                f"Creating vehicle with data: {vehicle_vals}")

                            # Create the vehicle
                            try:
                                vehicle = self.env['dealership.vehicle'].create(
                                    vehicle_vals)
                                _logger.info(
                                    f"Successfully created vehicle: {vehicle.name} with VIN: {vehicle.vin_number}")

                                # Post message to picking
                                picking.message_post(
                                    body=f"Created dealership vehicle: {vehicle.name} (VIN: {lot.name})"
                                )

                            except Exception as e:
                                _logger.error(
                                    f"Error creating vehicle: {str(e)}")
                                # Optionally raise the error or continue processing other lines
                                # raise
                        else:
                            _logger.info(
                                f"Vehicle with VIN {lot.name} already exists, skipping creation")

    def button_validate(self):
        """Override validate button to create vehicles after validation"""
        res = super(StockPicking, self).button_validate()

        for picking in self:
            if picking.picking_type_id.code == 'outgoing':  # Delivery to customer
                for move_line in picking.move_line_ids:
                    lot = move_line.lot_id  # VIN
                    product = move_line.product_id

                    if lot:
                        # Find matching dealership.vehicle
                        vehicle = self.env['dealership.vehicle'].search(
                            [('vin_number', '=', lot.name)], limit=1
                        )
                        if vehicle and vehicle.state != 'sold':
                            vehicle.write({'state': 'sold'})
                            _logger.info(
                                f"Vehicle {vehicle.name} with VIN {lot.name} marked as Sold.")
                            picking.message_post(
                                body=f"Vehicle {vehicle.name} (VIN: {lot.name}) marked as Sold."
                            )

        # Only create vehicles for successful validations
        if res:
            try:
                self.create_dealership_vehicles_from_receipt()
            except Exception as e:
                _logger.error(f"Error creating dealership vehicles: {str(e)}")
                # Optionally show user error or handle gracefully

        return res

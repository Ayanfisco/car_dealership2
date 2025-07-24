from odoo import models, api, fields, _
from odoo.exceptions import UserError

class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    @api.model
    def create(self, vals):
        line = super().create(vals)
        product = line.product_id.product_tmpl_id
        if product.is_vehicle:
            # Find or create dealership.vehicle record
            dealership_vehicle = line.env['dealership.vehicle'].search([
                ('make_id', '=', product.make_id.id),
                ('model_id', '=', product.model_id.id),
                ('year', '=', getattr(product, 'year', False)),
                ('color', '=', getattr(line.product_id, 'color', False)),
            ], limit=1)
            qty = line.product_qty
            if dealership_vehicle:
                dealership_vehicle.quantity += qty
            else:
                line.env['dealership.vehicle'].create({
                    'name': product.name,
                    'make_id': product.make_id.id,
                    'model_id': product.model_id.id,
                    'year': getattr(product, 'year', False),
                    'color': getattr(line.product_id, 'color', False),
                    'quantity': qty,
                })
        return line

    def action_create_fleet_vehicles(self):
        """Create fleet vehicles from this purchase order line after receipt"""
        for line in self:
            if line.product_id.is_vehicle:
                # Check if the PO line has been received
                if line.qty_received == 0:
                    raise UserError(_('No items have been received for this purchase order line yet.'))
                
                created_vehicles = line.product_id.product_tmpl_id.create_fleet_vehicles_from_purchase([line.id])
                if created_vehicles:
                    return {
                        'type': 'ir.actions.act_window',
                        'name': _('Created Fleet Vehicles'),
                        'res_model': 'fleet.vehicle',
                        'view_mode': 'tree,form',
                        'domain': [('id', 'in', [v.id for v in created_vehicles])],
                        'target': 'current',
                    }
                else:
                    raise UserError(_('No fleet vehicles were created. They may already exist or no serial numbers found.'))
        return {'type': 'ir.actions.act_window_close'}

    def action_view_fleet_vehicles(self):
        """View fleet vehicles created from this purchase order line"""
        # Find all fleet vehicles created from this PO line's serial numbers
        move_lines = self.move_ids.mapped('move_line_ids').filtered(
            lambda ml: ml.lot_id and ml.state == 'done'
        )
        
        if not move_lines:
            raise UserError(_('No received items with serial numbers found.'))
        
        serial_numbers = move_lines.mapped('lot_id.name')
        fleet_vehicles = self.env['fleet.vehicle'].search([
            ('vin_sn', 'in', serial_numbers)
        ])
        
        if not fleet_vehicles:
            raise UserError(_('No fleet vehicles found for the serial numbers from this purchase order line.'))
        
        return {
            'type': 'ir.actions.act_window',
            'name': _('Fleet Vehicles from PO Line'),
            'res_model': 'fleet.vehicle',
            'view_mode': 'tree,form',
            'domain': [('id', 'in', fleet_vehicles.ids)],
            'target': 'current',
        }

    def get_received_serial_numbers(self):
        """Get all serial numbers received for this purchase order line"""
        move_lines = self.move_ids.mapped('move_line_ids').filtered(
            lambda ml: ml.lot_id and ml.state == 'done' and ml.location_dest_id.usage == 'internal'
        )
        return move_lines.mapped('lot_id.name')

    def get_fleet_vehicles_count(self):
        """Get count of fleet vehicles created from this PO line"""
        serial_numbers = self.get_received_serial_numbers()
        if serial_numbers:
            return len(self.env['fleet.vehicle'].search([('vin_sn', 'in', serial_numbers)]))
        return 0
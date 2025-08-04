from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError

class FleetVehicle(models.Model):
    _inherit = 'fleet.vehicle'

    sale_order_id = fields.Many2one('sale.order', string='Sale Order', ondelete='set null')
    is_test_drive = fields.Boolean('In Test Drive', default=False)
    next_available_date = fields.Datetime('Next Available Date')
    last_test_drive_date = fields.Datetime('Last Test Drive Date')
    
    def action_set_in_preparation(self):
        self.ensure_one()
        if self.state_id.name != 'New':
            raise UserError(_("Only new vehicles can be set to preparation state."))
        prep_state = self.env.ref('car_dealership.fleet_vehicle_state_in_preparation')
        self.write({'state_id': prep_state.id})

    def action_set_available(self):
        self.ensure_one()
        if self.state_id.name not in ['In Preparation', 'Test Drive', 'Reserved']:
            raise UserError(_("Invalid state transition to Available."))
        available_state = self.env.ref('fleet.fleet_vehicle_state_registered')
        self.write({
            'state_id': available_state.id,
            'is_test_drive': False
        })

    def action_set_reserved(self):
        self.ensure_one()
        if self.state_id.name not in ['Registered', 'Test Drive']:
            raise UserError(_("Only available or test drive vehicles can be reserved."))
        reserved_state = self.env.ref('car_dealership.fleet_vehicle_state_reserved')
        self.write({
            'state_id': reserved_state.id,
            'is_test_drive': False
        })

    def action_start_test_drive(self):
        self.ensure_one()
        if self.state_id.name not in ['Registered', 'Reserved']:
            raise UserError(_("Only available or reserved vehicles can be taken for test drive."))
        test_drive_state = self.env.ref('car_dealership.fleet_vehicle_state_test_drive')
        self.write({
            'state_id': test_drive_state.id,
            'is_test_drive': True,
            'last_test_drive_date': fields.Datetime.now()
        })

    def action_end_test_drive(self):
        self.ensure_one()
        if not self.is_test_drive:
            raise UserError(_("Vehicle is not in test drive."))
        # Return to previous state (available or reserved)
        previous_state = self.env.ref('car_dealership.fleet_vehicle_state_reserved') \
            if self.sale_order_id else self.env.ref('fleet.fleet_vehicle_state_registered')
        self.write({
            'state_id': previous_state.id,
            'is_test_drive': False,
            'next_available_date': fields.Datetime.now()
        })

    def action_mark_as_sold(self):
        self.ensure_one()
        if not self.sale_order_id or self.sale_order_id.state != 'sale':
            raise UserError(_("Cannot mark as sold without a confirmed sale order."))
        sold_state = self.env.ref('fleet.fleet_vehicle_state_sold')
        self.write({'state_id': sold_state.id})

    def action_mark_as_delivered(self):
        self.ensure_one()
        if self.state_id.name != 'Sold':
            raise UserError(_("Only sold vehicles can be marked as delivered."))
        delivered_state = self.env.ref('car_dealership.fleet_vehicle_state_delivered')
        self.write({'state_id': delivered_state.id})

    @api.constrains('state_id', 'is_test_drive')
    def _check_state_constraints(self):
        for vehicle in self:
            if vehicle.is_test_drive and vehicle.state_id.name != 'Test Drive':
                raise ValidationError(_("Vehicle marked as in test drive must be in Test Drive state."))
    
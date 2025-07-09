from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
import logging

_logger = logging.getLogger(__name__)


class DealershipVehicle(models.Model):
    """Extended vehicle model for dealership operations"""
    _name = 'dealership.vehicle'
    _description = 'Dealership Vehicle'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc'

    name = fields.Char('Vehicle Name', tracking=True)
    vin_number = fields.Char('VIN Number', tracking=True, help="Vehicle Identification Number")
    fleet_vehicle_id = fields.Many2one('fleet.vehicle', string='Fleet Vehicle', ondelete='cascade')
    product_id = fields.Many2one('product.product', string='Product', ondelete='cascade')

    # Business Type
    business_type = fields.Selection([
        ('owner', 'Owner Product'),
        ('dealer_network', 'Dealer Network Product'),
        ('consigned', 'Consigned Product')
    ], string='Business Type', required=True, default='owner', tracking=True)

    # Vehicle Details
    make_id = fields.Many2one('fleet.vehicle.model.brand', string='Make', required=True)
    model_id = fields.Many2one('fleet.vehicle.model', string='Model', required=True)
    year = fields.Integer('Year', tracking=True)
    color = fields.Char('Color', tracking=True)
    engine_size = fields.Char('Engine Size', tracking=True, help="Engine size in liters or cc")
    mileage = fields.Float('Mileage (km)', tracking=True)
    fleet_category_id = fields.Many2one('fleet.vehicle.model.category', string='Body Type')
    fuel_type = fields.Selection([
        ('petrol', 'Petrol'),
        ('gasoline', 'Gasoline'),
        ('diesel', 'Diesel'),
        ('hybrid', 'Hybrid'),
        ('electric', 'Electric'),
        ('cng', 'CNG'),
        ('other', 'Other')
    ], string='Fuel Type', tracking=True)
    condition = fields.Selection([
        ('new', 'Brand New'),
        ('foreign_used', 'Foreign Used'),
        ('local_used', 'Local Used')
    ])
    transmission = fields.Selection([
        ('amt', 'AMT'),
        ('manual', 'Manual'),
        ('automatic', 'Automatic'),
        ('cvt', 'CVT')
    ], string='Transmission', tracking=True)

    # Financial Information
    purchase_price = fields.Monetary('Cost Price', currency_field='currency_id', tracking=True)
    selling_price = fields.Monetary('Selling Price', currency_field='currency_id', tracking=True)
    currency_id = fields.Many2one('res.currency', string='Currency',
                                  default=lambda self: self.env.company.currency_id)
    sale_order_line_id = fields.Many2one('sale.order.line', string='Sale Order Line')

    # Commission fields for dealer network and consigned products
    commission_type = fields.Selection([
        ('percentage', 'Percentage'),
        ('fixed', 'Fixed Amount')
    ], string='Commission Type', tracking=True)
    commission_value = fields.Float('Commission Value', tracking=True)
    commission_amount = fields.Monetary('Commission Amount', currency_field='currency_id',
                                        compute='_compute_commission_amount', store=True)
    net_payable = fields.Monetary('Net Payable', currency_field='currency_id',
                                  compute='_compute_net_payable', store=True)

    # Status
    state = fields.Selection([
        ('available', 'Available'),
        ('reserved', 'Reserved'),
        ('sold', 'Sold'),
        ('returned', 'Returned')
    ], string='Status', default='available', tracking=True)

    # Relations
    vendor_id = fields.Many2one('res.partner', string='Vendor/Consignor',
                                help="Dealer or consignor for non-owner products")
    purchase_order_line_id = fields.Many2one('purchase.order.line', string='Purchase Order Line')

    # Images and Documents
    image_1920 = fields.Image('Image', max_width=1920, max_height=1920)
    image_128 = fields.Image('Image 128', related='image_1920', max_width=128, max_height=128, store=True)

    # Computed fields
    profit_amount = fields.Monetary('Profit Amount', currency_field='currency_id',
                                    compute='_compute_profit_amount', store=True)
    profit_percentage = fields.Float('Profit %', compute='_compute_profit_percentage', store=True)

    # Quantity field
    quantity = fields.Integer('Quantity', default=1, tracking=True, help="Number of vehicles of this make/model/year/color in stock.")

    # Add SQL constraint to prevent duplicates at database level
    _sql_constraints = [
        ('unique_model_year', 'UNIQUE(model_id, year)',
         'A vehicle with this model and year already exists in the system!')
    ]

   

    @api.onchange('make_id')
    def _onchange_make_id(self):
        """Clear model when make changes"""
        if self.make_id:
            # Clear the model field and set domain
            self.model_id = False
            return {'domain': {'model_id': [('brand_id', '=', self.make_id.id)]}}
        else:
            # If no make selected, clear model and show no models
            self.model_id = False
            return {'domain': {'model_id': [('id', '=', False)]}}

    @api.onchange('model_id', 'year', 'color')
    def _onchange_vehicle_details(self):
        if self.model_id:
            name_parts = [self.model_id.brand_id.name, self.model_id.name]
            if self.year:
                name_parts.append(str(self.year))
            if self.color:
                name_parts.append(self.color)
            self.name = ' '.join(name_parts)

    @api.constrains('vin_number')
    def _check_vin_number(self):
        for record in self:
            if record.vin_number:
                existing = self.search([
                    ('vin_number', '=', record.vin_number),
                    ('id', '!=', record.id)
                ])
                if existing:
                    raise ValidationError(_('VIN Number must be unique. This VIN already exists.'))

    @api.constrains('model_id', 'year')
    def _check_duplicate_model_year(self):
        """Check for duplicate model and year combination"""
        for record in self:
            if record.model_id and record.year:
                existing = self.search([
                    ('model_id', '=', record.model_id.id),
                    ('year', '=', record.year),
                    ('id', '!=', record.id)
                ])
                if existing:
                    raise ValidationError(
                        _('A vehicle with model "%s" and year "%s" already exists in the system.\n'
                          'Existing vehicle: %s') %
                        (record.model_id.name, record.year, existing[0].name)
                    )

    @api.constrains('business_type', 'vendor_id', 'commission_type', 'commission_value')
    def _check_business_type_requirements(self):
        for record in self:
            if record.business_type in ['dealer_network', 'consigned']:
                if not record.vendor_id:
                    raise ValidationError(_('Vendor/Consignor is required for %s products.') %
                                          record.business_type.replace('_', ' ').title())
                if not record.commission_type or not record.commission_value:
                    raise ValidationError(_('Commission type and value are required for %s products.') %
                                          record.business_type.replace('_', ' ').title())

    def action_reserve(self):
        """Reserve the vehicle"""
        self.write({'state': 'reserved'})
        self.message_post(body=_('Vehicle has been reserved.'))

    def action_make_available(self):
        """Make the vehicle available again"""
        self.write({'state': 'available'})
        self.message_post(body=_('Vehicle is now available for sale.'))

    def action_mark_sold(self):
        """Mark the vehicle as sold"""
        self.write({'state': 'sold'})
        self.message_post(body=_('Vehicle has been sold.'))

    def action_return_vehicle(self):
        """Return consigned vehicle to owner"""
        if self.business_type != 'consigned':
            raise UserError(_('Only consigned vehicles can be returned.'))
        self.write({'state': 'returned'})
        self.message_post(body=_('Vehicle has been returned to consignor.'))

    def create_fleet_vehicle(self):
        """Create corresponding fleet vehicle record"""
        if not self.fleet_vehicle_id:
            fleet_vals = {
                'model_id': self.model_id.id,
                'license_plate': self.vin_number or '',
                'vin_sn': self.vin_number,
                'color': self.color,
                'odometer': self.mileage,
                # 'fuel_type': self.fuel_type,
                'transmission': self.transmission,
                # 'engine_size': self.engine_size,
                'category_id': self.fleet_category_id,
                'model_year': self.year,
                'acquisition_date': fields.Date.today(),
                'car_value': self.purchase_price,
            }
            fleet_vehicle = self.env['fleet.vehicle'].create(fleet_vals)
            self.fleet_vehicle_id = fleet_vehicle.id
            self.message_post(body=_('Fleet vehicle record created: %s') % fleet_vehicle.name)

    def unlink(self):
        """Override unlink to handle product deletion"""
        products_to_delete = self.product_id
        result = super().unlink()
        # Delete corresponding products if they exist
        if products_to_delete:
            products_to_delete.unlink()
        return result

    def _send_maintenance_reminders(self):
        # Example: log a message for demonstration
        _logger.info('Scheduled: Maintenance reminders sent for dealership vehicles.')
        # Implement actual reminder logic here
        return True
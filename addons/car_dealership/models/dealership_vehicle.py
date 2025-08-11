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

    name = fields.Char('Vehicle Name', required=True, tracking=False)
    is_template_dummy = fields.Boolean(
        'Is Template Dummy', default=True,)
    vin_number = fields.Char('VIN Number', tracking=True,
                             help="Vehicle Identification Number")
    fleet_vehicle_id = fields.Many2one(
        'fleet.vehicle', string='Fleet Vehicle', ondelete='cascade')
    product_id = fields.Many2one(
        'product.product', string='Product', ondelete='cascade')

    # Vehicle Details
    make_id = fields.Many2one(
        'fleet.vehicle.model.brand', string='Make', required=False)
    model_id = fields.Many2one(
        'fleet.vehicle.model', string='Model', tracking=True, required=False)
    year = fields.Integer('Year', tracking=True)
    color = fields.Char('Color', tracking=True)
    engine_size = fields.Char(
        'Engine Size', tracking=True, help="Engine size in liters or cc")
    mileage = fields.Float('Mileage (km)', tracking=True)
    fleet_category_id = fields.Many2one(
        'fleet.vehicle.model.category', string='Body Type')
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
    purchase_price = fields.Monetary(
        'Cost Price', currency_field='currency_id', tracking=True)
    selling_price = fields.Monetary(
        'Selling Price', currency_field='currency_id', tracking=True)
    currency_id = fields.Many2one('res.currency', string='Currency',
                                  default=lambda self: self.env.company.currency_id)
    sale_order_line_id = fields.Many2one(
        'sale.order.line', string='Sale Order Line')

    # Status
    state = fields.Selection([
        ('draft', 'Draft'),
        ('available', 'Available'),
        ('sold', 'Sold'),
    ], string='Status', default='draft', tracking=True)

    # Relations
    vendor_id = fields.Many2one('res.partner', string='Vendor/Consignor',
                                help="Dealer or consignor for non-owner products")
    purchase_order_line_id = fields.Many2one(
        'purchase.order.line', string='Purchase Order Line')

    # Images and Documents
    image_1920 = fields.Image('Image', max_width=1920, max_height=1920)
    image_128 = fields.Image(
        'Image 128', related='image_1920', max_width=128, max_height=128, store=True)

    # Quantity field
    quantity = fields.Integer('Quantity', default=1, tracking=True,
                              help="Number of vehicles of this make/model/year/color in stock.")

    # Add SQL constraint to prevent duplicates at database level
    _sql_constraints = [
        ('unique_model_year', 'UNIQUE(model_id, year)',
         'A vehicle with this model and year already exists in the system!')
    ]

    @api.model_create_multi
    def create(self, vals_list):
        new_vehicles = self.env['dealership.vehicle']
        for vals in vals_list:
            # Always create individual records when called from stock picking with VIN
            # This ensures each serial number creates a separate vehicle record
            new_vehicle = super(DealershipVehicle, self).create([vals])

            # Create product only if it doesn't exist
            if not new_vehicle.product_id:
                new_vehicle._create_product()

            new_vehicles += new_vehicle

        return new_vehicles

    def _create_product(self):
        """Create corresponding product template for the dealership vehicle"""
        if self.product_id:
            return  # Product already exists

        category = self.env.ref(
            'car_dealership.product_category_dealership_vehicles')

        # Prepare product template values
        product_vals = {
            'name': self.name,
            'type': 'consu',  # For Odoo 16+ use 'detailed_type'
            'make_id': self.make_id.id if self.make_id and hasattr(self.make_id, 'id') else False,
            'model_id': self.model_id.id if self.model_id and hasattr(self.model_id, 'id') else False,
            'year': self.year,
            'tracking': 'serial',  # Track by unique serial number (VIN)
            'categ_id': category.id,
            'list_price': self.selling_price or 0.0,
            'standard_price': self.purchase_price or 0.0,
            'is_vehicle': True,
            'is_storable': True,
            # Add custom fields if they exist in your product.template model
        }

        # Create the product template
        product_template = self.env['product.template'].create(product_vals)

        # Get the corresponding product.product (first variant)
        product_product = product_template.product_variant_id

        # Link the product.product to this vehicle
        self.product_id = product_product.id

        self.message_post(body=_('Product created: %s') %
                          product_template.name)

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

    @api.onchange('model_id', 'year')
    def _onchange_vehicle_details(self):
        if self.model_id:
            name_parts = [self.model_id.brand_id.name, self.model_id.name]
            if self.year:
                name_parts.append(str(self.year))
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
                    raise ValidationError(
                        _('VIN Number must be unique. This VIN already exists.'))

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
                'state_id': self.env['fleet.vehicle.state'].search([('name', '=', 'Unregistered')], limit=1).id,
            }
            fleet_vehicle = self.env['fleet.vehicle'].create(fleet_vals)
            self.fleet_vehicle_id = fleet_vehicle.id
            self.message_post(
                body=_('Fleet vehicle record created: %s') % fleet_vehicle.name)

    def unlink(self):
        """Override unlink to handle product deletion"""
        products_to_delete = self.product_id
        result = super().unlink()
        # Delete corresponding products if they exist
        if products_to_delete:
            products_to_delete.unlink()
        return result

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
import logging

_logger = logging.getLogger(__name__)


class DealershipVehicle(models.Model):
    """Extended vehicle model for dealership operations"""
    _name = 'dealership.vehicle'
    _description = 'Dealership Vehicle'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'is_favorite desc, create_date desc'

    name = fields.Char('Vehicle Name', required=True, tracking=False,
                       help="Name of the vehicle, usually a combination of make, model, and year.")
    is_template_dummy = fields.Boolean(
        'Is Template Dummy', default=True,)
    is_favorite = fields.Boolean(
        'Is Favorite', default=False, tracking=True)
    vin_number = fields.Char('VIN Number', tracking=True,
                             help="Vehicle Identification Number")
    fleet_vehicle_id = fields.Many2one(
        'fleet.vehicle', string='Fleet Vehicle', ondelete='cascade')
    product_id = fields.Many2one(
        'product.product', string='Product', ondelete='cascade')

    product_template_id = fields.Many2one(
        'product.template', string='Product Template', ondelete='cascade')

    # Vehicle Details
    make_id = fields.Many2one(
        'fleet.vehicle.model.brand', string='Make', required=True, tracking=True)
    model_id = fields.Many2one(
        'fleet.vehicle.model', string='Model', tracking=True, required=True)
    year = fields.Integer(string='Year', tracking=True, required=True)
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

    dealership_image_ids = fields.Many2many(
        'ir.attachment',
        'dealership_vehicle_image_rel',
        'dealership_vehicle_id', 'attachment_id',
        string='Dealership Images',
        domain="[('mimetype', 'ilike', 'image')]",
        help='Upload multiple images for this product.'
    )

    dealership_video_ids = fields.Many2many(
        'ir.attachment',
        'dealership_vehicle_video_rel',
        'dealership_vehicle_id', 'attachment_id',
        string='Dealership Videos',
        domain="[('mimetype', 'ilike', 'video')]",
        help='Upload multiple videos for this product.'
    )

    # Quantity field
    quantity = fields.Integer('Quantity', default=1, tracking=True,
                              help="Number of vehicles of this make/model/year/color in stock.")
    trim = fields.Char('Trim', tracking=True,)

    @api.model
    def create_product_variant(self):
        # Create specific product variant when vehicle becomes available
        variant = self.product_id.create_variant({
            'name': f"{self.product_id.name} - {self.vin_number}",
            'default_code': self.vin_number,
        })
        self.product_variant_id = variant.id

    @api.model_create_multi
    def create(self, vals_list):
        new_vehicles = self.env['dealership.vehicle']
        for vals in vals_list:
            # Always create individual records when called from stock picking with VIN
            # This ensures each serial number creates a separate vehicle record
            new_vehicle = super(DealershipVehicle, self).create([vals])
            if not new_vehicle.year:
                raise UserError(_('Year is required.'))
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
        if self.is_template_dummy:
            product_vals = {
                'name': self.name,
                'type': 'consu',  # For Odoo 16+ use 'detailed_type'
                'make_id': self.make_id.id if self.make_id else False,
                'model_id': self.model_id.id if self.model_id else False,
                'year': self.year,
                'tracking': 'serial',  # Track by unique serial number (VIN)
                'categ_id': category.id,
                'list_price': self.selling_price or 0.0,
                'standard_price': self.purchase_price or 0.0,
                'is_vehicle': True,
                'is_storable': True,
                'image_1920': self.image_1920,
                # Add custom fields if they exist in your product.template model
            }

            # Create the product template
            product_template = self.env['product.template'].create(
                product_vals)

            # Get the corresponding product.product (first variant)
            product_product = product_template.product_variant_id

            # Link the product.product to this vehicle
            self.product_id = product_product.id

            self.message_post(body=_('Product created: %s') %
                              product_template.name)

        elif not self.is_template_dummy:
            # Find existing product template with same model and year
            existing_template = self.env['product.template'].search([
                ('model_id', '=', self.model_id.id if self.model_id else False),
                ('year', '=', self.year),
                ('is_vehicle', '=', True),
                ('active', '=', True)  # Only search active templates
            ], limit=1)

            if existing_template and hasattr(self, 'trim') and self.trim:
                # Create variant for existing template
                variant = self._create_product_variant(existing_template)
                if variant:
                    self.product_id = variant.id
                    self.message_post(
                        body=_('Product variant created: %s') % variant.display_name)
                    return

            # If no existing template found or variant creation failed, create new template
            product_vals = {
                'name': f"{self.model_id.name} {self.year}" if self.model_id else self.name,
                'type': 'consu',
                'make_id': self.make_id.id if self.make_id else False,
                'model_id': self.model_id.id if self.model_id else False,
                'year': self.year,
                'tracking': 'serial',  # Track by unique serial number (VIN)
                'categ_id': category.id,
                'list_price': self.selling_price or 0.0,
                'standard_price': self.purchase_price or 0.0,
                'is_vehicle': True,
                'is_storable': True,
                'image_1920': self.image_1920,
                'active': True,  # Keep template active for variants
            }

            product_template = self.env['product.template'].create(
                product_vals)

            # If we have trim information, create variant
            if hasattr(self, 'trim') and self.trim:
                variant = self._create_product_variant(product_template)
                if variant:
                    self.product_id = variant.id
                    self.message_post(
                        body=_('Product template and variant created: %s') % variant.display_name)
                else:
                    # Fallback to default variant
                    self.product_id = product_template.product_variant_id.id
                    self.message_post(
                        body=_('Product template created: %s') % product_template.name)
            else:
                # No trim info, use default variant
                self.product_id = product_template.product_variant_id.id
                self.message_post(
                    body=_('Product template created: %s') % product_template.name)

    def _create_product_variant(self, product_template):
        """Create a product variant with trim information"""
        if not hasattr(self, 'trim') or not self.trim:
            return None

        try:
            # Get or create Trim attribute
            trim_attribute = self.env['product.attribute'].search([
                ('name', '=', 'Trim')
            ], limit=1)

            if not trim_attribute:
                trim_attribute = self.env['product.attribute'].create({
                    'name': 'Trim',
                    'display_type': 'radio',
                    'create_variant': 'always'
                })

            # Get or create trim attribute value
            trim_attribute_value = self.env['product.attribute.value'].search([
                ('attribute_id', '=', trim_attribute.id),
                ('name', '=', self.trim)
            ], limit=1)

            if not trim_attribute_value:
                trim_attribute_value = self.env['product.attribute.value'].create({
                    'attribute_id': trim_attribute.id,
                    'name': self.trim,
                    'sequence': 1
                })

            # Check if template has trim attribute line
            template_attribute_line = self.env['product.template.attribute.line'].search([
                ('product_tmpl_id', '=', product_template.id),
                ('attribute_id', '=', trim_attribute.id)
            ], limit=1)

            if not template_attribute_line:
                # Add trim attribute to product template
                template_attribute_line = self.env['product.template.attribute.line'].create({
                    'product_tmpl_id': product_template.id,
                    'attribute_id': trim_attribute.id,
                    'value_ids': [(6, 0, [trim_attribute_value.id])]
                })
            else:
                # Add the new trim value to existing attribute line if not already present
                if trim_attribute_value.id not in template_attribute_line.value_ids.ids:
                    template_attribute_line.write({
                        'value_ids': [(4, trim_attribute_value.id)]
                    })

            # Create product template attribute value if not exists
            template_attribute_value = self.env['product.template.attribute.value'].search([
                ('product_tmpl_id', '=', product_template.id),
                ('attribute_id', '=', trim_attribute.id),
                ('product_attribute_value_id', '=', trim_attribute_value.id)
            ], limit=1)

            if not template_attribute_value:
                template_attribute_value = self.env['product.template.attribute.value'].create({
                    'product_tmpl_id': product_template.id,
                    'attribute_id': trim_attribute.id,
                    'product_attribute_value_id': trim_attribute_value.id,
                    'price_extra': 0.0
                })

            # Force creation of product variants
            product_template._create_variant_ids()

            # Find the specific variant with our trim
            variant = self.env['product.product'].search([
                ('product_tmpl_id', '=', product_template.id),
                ('product_template_attribute_value_ids',
                 'in', template_attribute_value.ids)
            ], limit=1)

            return variant

        except Exception as e:
            _logger.error(
                f"Error creating product variant with trim {self.trim}: {str(e)}")
            return None

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

    @api.onchange('model_id', 'year', 'trim')
    def _onchange_vehicle_details(self):
        if self.model_id:
            name_parts = [self.model_id.brand_id.name, self.model_id.name]
            if self.year:
                name_parts.append(str(self.year))
            if self.trim:
                name_parts.append(str(self.trim))
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

    # Add 'state' to the constrains decorator
    @api.constrains('model_id', 'year', 'state')
    def _check_duplicate_model_year(self):
        """Check for duplicate model and year combination for draft vehicles"""
        for record in self:
            # Only apply constraint to draft vehicles
            if record.state == 'draft' and record.model_id and record.year:
                existing = self.search([
                    ('model_id', '=', record.model_id.id),
                    ('year', '=', record.year),
                    # Only check against other draft vehicles
                    ('state', '=', 'draft'),
                    ('id', '!=', record.id)
                ])
                if existing:
                    raise ValidationError(
                        _('A draft vehicle with model "%s" and year "%s" already exists in the system.\n'
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

    def _update_product(self):
        """Update corresponding product template with vehicle information"""
        if not self.product_id:
            return

        # Get the product template from the product variant
        product_template = self.product_id.product_tmpl_id

        # Get the appropriate product category
        category = self.env.ref(
            'car_dealership.product_category_dealership_vehicles')
        if self.is_template_dummy:

            update_vals = {
                'name': self.name,
                'type': 'consu',
                'make_id': self.make_id.id if self.make_id else False,
                'model_id': self.model_id.id if self.model_id else False,
                'year': self.year,
                'tracking': 'serial',  # Track by unique serial number (VIN)
                'categ_id': category.id,
                'list_price': self.selling_price or 0.0,
                'standard_price': self.purchase_price or 0.0,
                'is_vehicle': True,
                'is_storable': True,
                'image_1920': self.image_1920,
            }

            product_template.write(update_vals)

        elif not self.is_template_dummy:
            update_vals = {
                'name': self.name,
                'type': 'consu',
                'make_id': self.make_id.id if self.make_id else False,
                'model_id': self.model_id.id if self.model_id else False,
                'year': self.year,
                'tracking': 'serial',  # Track by unique serial number (VIN)
                'categ_id': category.id,
                'list_price': self.selling_price or 0.0,
                'standard_price': self.purchase_price or 0.0,
                'is_vehicle': True,
                'is_storable': True,
                'image_1920': self.image_1920,
                'active': False,
            }

            product_template.write(update_vals)

    @api.model
    def

    def write(self, vals):
        """Override write to update corresponding product"""
        result = super().write(vals)

        # Update product if certain fields change
        update_product_fields = [
            'name', 'selling_price', 'purchase_price', 'business_type']
        if any(field in vals for field in update_product_fields):
            for vehicle in self:
                vehicle._update_product()

        return result

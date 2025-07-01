from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class DealershipVehicle(models.Model):
    """Extended vehicle model for dealership operations"""
    _name = 'dealership.vehicle'
    _description = 'Dealership Vehicle'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc'

    name = fields.Char('Vehicle Name', required=True, tracking=True)
    vin_number = fields.Char('VIN Number', tracking=True, help="Vehicle Identification Number")
    fleet_vehicle_id = fields.Many2one('fleet.vehicle', string='Fleet Vehicle', ondelete='cascade')
    product_id = fields.Many2one('product.product', string='Product', ondelete='cascade')

    # Business Type
    business_type = fields.Selection([
        ('owner', 'Owner Product'),
        # ('dealer_network', 'Dealer Network Product'),
        # ('consigned', 'Consigned Product')
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

    @api.model_create_multi
    def create(self, vals_list):
        """Override create to automatically create corresponding product"""
        # Create the dealership vehicles first
        vehicles = super().create(vals_list)

        # Create corresponding products for each vehicle
        for vehicle in vehicles:
            vehicle._create_product()

        return vehicles

    def _create_product(self):
        """Create corresponding product template for the dealership vehicle"""
        if self.product_id:
            return  # Product already exists

        # Get the appropriate product category
        category = self._get_product_category()

        # Prepare product template values
        product_vals = {
            'name': self.name,
            'type': 'consu',  # For Odoo 16+ use 'detailed_type'
            'tracking': 'serial',  # Track by unique serial number (VIN)
            'categ_id': category.id if category else False,
            'list_price': self.selling_price or 0.0,
            'standard_price': self.purchase_price or 0.0,
            # Add custom fields if they exist in your product.template model
            'is_dealership_vehicle': True,
            'dealership_business_type': self.business_type,
            'vehicle_make_id': self.make_id.id if self.make_id else False,
            'vehicle_model_id': self.model_id.id if self.model_id else False,
            'default_commission_type': self.commission_type,
            'default_commission_value': self.commission_value,
            'default_vendor_id': self.vendor_id.id if self.vendor_id else False,
        }

        # Create the product template
        product_template = self.env['product.template'].create(product_vals)

        # Get the corresponding product.product (first variant)
        product_product = product_template.product_variant_id

        # Link the product.product to this vehicle
        self.product_id = product_product.id

        self.message_post(body=_('Product created: %s') % product_template.name)

    def _update_product(self):
        """Update corresponding product template with vehicle information"""
        if not self.product_id:
            return

        # Get the product template from the product variant
        product_template = self.product_id.product_tmpl_id

        # Get the appropriate product category
        category = self._get_product_category()

        update_vals = {
            'name': self.name,
            'list_price': self.selling_price or 0.0,
            'standard_price': self.purchase_price or 0.0,
            'categ_id': category.id if category else product_template.categ_id.id,
            # Add custom fields if they exist in your product.template model
            'is_dealership_vehicle': True,
            'dealership_business_type': self.business_type,
            'vehicle_make_id': self.make_id.id if self.make_id else False,
            'vehicle_model_id': self.model_id.id if self.model_id else False,
            'default_commission_type': self.commission_type,
            'default_commission_value': self.commission_value,
            'default_vendor_id': self.vendor_id.id if self.vendor_id else False,
        }

        product_template.write(update_vals)

    def _get_product_category(self):
        """Get product category based on business type"""
        category_mapping = {
            'owner': 'Owner Products',
            'dealer_network': 'Dealer Network Products',
            'consigned': 'Consigned Products'
        }
        category_name = category_mapping.get(self.business_type, 'Dealership Vehicles')

        # Try to find the specific category first
        category = self.env['product.category'].search([
            ('name', '=', category_name)
        ], limit=1)

        # If not found, try to find the parent category
        if not category:
            category = self.env['product.category'].search([
                ('name', '=', 'Dealership Vehicles')
            ], limit=1)

        return category

    def write(self, vals):
        """Override write to update corresponding product"""
        result = super().write(vals)

        # Update product if certain fields change
        update_product_fields = ['name', 'selling_price', 'purchase_price', 'business_type']
        if any(field in vals for field in update_product_fields):
            for vehicle in self:
                vehicle._update_product()

        return result

    @api.depends('purchase_price', 'commission_type', 'commission_value')
    def _compute_commission_amount(self):
        for record in self:
            if record.business_type in ['dealer_network', 'consigned'] and record.purchase_price:
                if record.commission_type == 'percentage':
                    record.commission_amount = record.purchase_price * (record.commission_value / 100)
                elif record.commission_type == 'fixed':
                    record.commission_amount = record.commission_value
                else:
                    record.commission_amount = 0.0
            else:
                record.commission_amount = 0.0

    @api.depends('purchase_price', 'commission_amount')
    def _compute_net_payable(self):
        for record in self:
            if record.business_type in ['dealer_network', 'consigned']:
                record.net_payable = record.purchase_price - record.commission_amount
            else:
                record.net_payable = record.purchase_price

    @api.depends('selling_price', 'purchase_price', 'commission_amount', 'business_type')
    def _compute_profit_amount(self):
        for record in self:
            if record.selling_price and record.purchase_price:
                if record.business_type == 'owner':
                    record.profit_amount = record.selling_price - record.purchase_price
                elif record.business_type in ['dealer_network', 'consigned']:
                    record.profit_amount = record.selling_price - record.net_payable
                else:
                    record.profit_amount = 0.0
            else:
                record.profit_amount = 0.0

    @api.depends('profit_amount', 'purchase_price')
    def _compute_profit_percentage(self):
        for record in self:
            if record.purchase_price:
                record.profit_percentage = (record.profit_amount / record.purchase_price) * 100
            else:
                record.profit_percentage = 0.0

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
                'fuel_type': self.fuel_type,
                'transmission': self.transmission,
                'engine_size': self.engine_size,
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
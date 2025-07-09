from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
import logging


class ProductTemplate(models.Model):
    """Extended product template for dealership vehicles"""
    _inherit = 'product.template'

    # Dealership specific fields
    is_dealership_vehicle = fields.Boolean('Is Dealership Vehicle', default=False)
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
    is_storable = fields.Boolean('Is Storable', default=True, tracking=True)
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
        # ('amt', 'AMT'),
        ('manual', 'Manual'),
        ('automatic', 'Automatic'),
        # ('cvt', 'CVT')
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
    quantity = fields.Integer('Quantity', default=1, tracking=True,
                              help="Number of vehicles of this make/model/year/color in stock.")

    # Add SQL constraint to prevent duplicates at database level
    _sql_constraints = [
        ('unique_model_year', 'UNIQUE(model_id, year)',
         'A vehicle with this model and year already exists in the system!')
    ]
    is_vehicle = fields.Boolean('Is Vehicle', default=False,
                                help="Check if this product is a vehicle. If checked, a record will be created in both Fleet and Car Dealership modules.")

    @api.onchange('is_dealership_vehicle')
    def _onchange_is_dealership_vehicle(self):
        if self.is_dealership_vehicle:
            # Set default values for dealership vehicles
            self.type = 'consu'  # Use 'type' instead of 'detailed_type' for Odoo 18
            self.tracking = 'serial'  # Track by unique serial number (VIN)
            self.categ_id = self._get_default_dealership_category()
        else:
            self.business_type = False  # Fixed: Use 'business_type' instead of 'dealership_business_type'
            self.make_id = False  # Fixed: Use 'make_id' instead of 'vehicle_make_id'
            self.model_id = False  # Fixed: Use 'model_id' instead of 'vehicle_model_id'

    @api.onchange('model_id', 'year', 'color')
    def _onchange_vehicle_details(self):
        if self.model_id:
            name_parts = [self.model_id.brand_id.name, self.model_id.name]
            if self.year:
                name_parts.append(str(self.year))
            if self.color:
                name_parts.append(self.color)
            self.name = ' '.join(name_parts)

    @api.onchange('business_type')  # Fixed: Use 'business_type' instead of 'dealership_business_type'
    def _onchange_business_type(self):
        if self.business_type:
            category = self._get_dealership_category_by_type(self.business_type)
            if category:
                self.categ_id = category.id

    @api.onchange('make_id')  # Fixed: Use 'make_id' instead of 'vehicle_make_id'
    def _onchange_make_id(self):
        if self.make_id:
            return {'domain': {'model_id': [('brand_id', '=', self.make_id.id)]}}
        return {'domain': {'model_id': []}}

    @api.onchange('model_id')  # Fixed: Use 'model_id' instead of 'vehicle_model_id'
    def _onchange_model_id(self):
        if self.model_id and self.make_id:
            # Auto-generate product name
            self.name = f"{self.make_id.name} {self.model_id.name}"

    def _get_default_dealership_category(self):
        """Get default product category for dealership vehicles"""
        category = self.env['product.category'].search([
            ('name', '=', 'Dealership Vehicles')
        ], limit=1)
        return category

    def _get_dealership_category_by_type(self, business_type):
        """Get product category based on business type"""
        category_mapping = {
            'owner': 'Owner Products',
            'dealer_network': 'Dealer Network Products',
            'consigned': 'Consigned Products'
        }
        category_name = category_mapping.get(business_type)
        if category_name:
            return self.env['product.category'].search([
                ('name', '=', category_name)
            ], limit=1)
        return False

    @api.model
    def create(self, vals):
        if vals.get('is_vehicle'):
            vals['type'] = 'consu'  # Make it storable (Odoo 17+/18)
            vals['tracking'] = 'serial'  # Enable serial tracking
            # Check for existing template with same make/model/year
            domain = [
                ('is_vehicle', '=', True),
                ('make_id', '=', vals.get('make_id')),
                ('model_id', '=', vals.get('model_id')),
                ('year', '=', vals.get('year'))
            ]
            existing_template = self.env['product.template'].search(domain, limit=1)
            if existing_template:
                return existing_template
        product = super().create(vals)
        # Ensure all variants are storable if is_vehicle
        if product.is_vehicle:
            for variant in product.product_variant_ids:
                variant.type = 'consu'
        return product

    def write(self, vals):
        res = super().write(vals)
        for product in self:
            if vals.get('is_vehicle'):
                product.type = 'consu'
                for variant in product.product_variant_ids:
                    variant.type = 'consu'
            if vals.get('is_vehicle') and not self.env['dealership.vehicle'].search([('product_id', '=', product.id)]):
                product.type = 'consu'
                product.tracking = 'serial'
                # Create Fleet Vehicle if not exists
                fleet_vals = {
                    'model_id': product.model_id.id,  # Fixed: Use 'model_id' instead of 'vehicle_model_id'
                    'brand_id': product.make_id.id,  # Fixed: Use 'make_id' instead of 'vehicle_make_id'
                    'license_plate': product.name,
                }
                fleet_vehicle = self.env['fleet.vehicle'].create(fleet_vals)
                # Create Dealership Vehicle if not exists
                dealership_vals = {
                    'name': product.name,
                    'make_id': product.make_id.id,  # Fixed: Use 'make_id' instead of 'vehicle_make_id'
                    'model_id': product.model_id.id,  # Fixed: Use 'model_id' instead of 'vehicle_model_id'
                    'product_id': product.id,
                    'fleet_vehicle_id': fleet_vehicle.id,
                    'business_type': product.business_type or 'owner',
                    # Fixed: Use 'business_type' instead of 'dealership_business_type'
                }
                self.env['dealership.vehicle'].create(dealership_vals)
                # Create incoming stock move for inventory
                stock_location = self.env.ref('stock.stock_location_stock', raise_if_not_found=False)
                if stock_location:
                    self.env['stock.quant'].create({
                        'product_id': product.id,
                        'location_id': stock_location.id,
                        'quantity': 1.0,
                        'inventory_quantity': 1.0,
                    })
        return res

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

    # Add missing computed methods
    @api.depends('purchase_price', 'commission_value', 'commission_type')
    def _compute_commission_amount(self):
        for record in self:
            if record.commission_type == 'percentage':
                record.commission_amount = (record.purchase_price * record.commission_value) / 100
            elif record.commission_type == 'fixed':
                record.commission_amount = record.commission_value
            else:
                record.commission_amount = 0.0

    @api.depends('purchase_price', 'commission_amount')
    def _compute_net_payable(self):
        for record in self:
            record.net_payable = record.purchase_price - record.commission_amount

    @api.depends('selling_price', 'purchase_price')
    def _compute_profit_amount(self):
        for record in self:
            record.profit_amount = record.selling_price - record.purchase_price

    @api.depends('profit_amount', 'purchase_price')
    def _compute_profit_percentage(self):
        for record in self:
            if record.purchase_price:
                record.profit_percentage = (record.profit_amount / record.purchase_price) * 100
            else:
                record.profit_percentage = 0.0
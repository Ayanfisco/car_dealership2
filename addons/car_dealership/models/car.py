from odoo import models, fields, api
from odoo.exceptions import ValidationError
from datetime import date


class Car(models.Model):
    _name = 'car.dealership.car'
    _description = 'Car Inventory'
    _order = 'year desc, make_id, model_id'
    _rec_name = 'display_name'

    # Basic Information
    display_name = fields.Char('Display Name', compute='_compute_display_name', store=True)
    vin = fields.Char('VIN Number', required=True, size=17)
    make_id = fields.Many2one('car.dealership.make', string='Make', required=True)
    model_id = fields.Many2one('car.dealership.model', string='Model', required=True,
                               domain="[('make_id', '=', make_id)]")
    year = fields.Integer('Year', required=True)

    # Vehicle Details
    color_exterior = fields.Char('Exterior Color')
    color_interior = fields.Char('Interior Color')
    mileage = fields.Integer('Mileage (km)')
    engine_size = fields.Float('Engine Size (L)')
    fuel_type = fields.Selection([
        ('petrol', 'Petrol'),
        ('diesel', 'Diesel'),
        ('hybrid', 'Hybrid'),
        ('electric', 'Electric'),
        ('lpg', 'LPG'),
    ], string='Fuel Type')
    transmission = fields.Selection([
        ('manual', 'Manual'),
        ('automatic', 'Automatic'),
        ('cvt', 'CVT'),
    ], string='Transmission')

    # Condition & Status
    condition = fields.Selection([
        ('new', 'New'),
        ('used', 'Used'),
        ('certified', 'Certified Pre-Owned'),
    ], string='Condition', required=True, default='used')

    status = fields.Selection([
        ('available', 'Available'),
        ('reserved', 'Reserved'),
        ('sold', 'Sold'),
        ('leased', 'Leased'),
        ('service', 'In Service'),
        ('damaged', 'Damaged'),
    ], string='Status', default='available', required=True)

    # Pricing
    purchase_price = fields.Monetary('Cost Price', currency_field='currency_id')
    selling_price = fields.Monetary('Sales Price', currency_field='currency_id')
    lease_price_monthly = fields.Monetary('Monthly Lease Price', currency_field='currency_id')
    currency_id = fields.Many2one('res.currency', string='Currency',
                                  default=lambda self: self.env.company.currency_id)

    # Features & Options
    feature_ids = fields.Many2many('car.dealership.feature', string='Features')

    # Images & Documents
    image_main = fields.Binary('Main Image')
    image_ids = fields.One2many('car.dealership.image', 'car_id', string='Additional Images')

    # Location & Inventory
    location = fields.Char('Lot Location')
    date_acquired = fields.Date('Date Acquired', default=fields.Date.today)
    days_in_inventory = fields.Integer('Days in Inventory', compute='_compute_days_in_inventory')

    # Descriptions
    description = fields.Html('Description')
    internal_notes = fields.Text('Internal Notes')

    # Lease Options
    is_leaseable = fields.Boolean('Available for Lease', default=True)
    lease_term_min = fields.Integer('Minimum Lease Term (months)', default=12)
    lease_term_max = fields.Integer('Maximum Lease Term (months)', default=60)

    # Service & Warranty
    warranty_expiry = fields.Date('Warranty Expiry')
    last_service_date = fields.Date('Last Service Date')
    next_service_date = fields.Date('Next Service Date')
    service_history_ids = fields.One2many('car.dealership.service', 'car_id', string='Service History')

    # Relationships
    sale_order_id = fields.Many2one('sale.order', string='Sale Order')
    product_id = fields.Many2one('product.product', string='Product')
    lease_id = fields.Many2one('car.dealership.lease', string='Current Lease')
    owner_id = fields.Many2one('res.partner', string='Current Owner')

    # Computed Fields
    age = fields.Integer('Age (Years)', compute='_compute_age')
    is_available = fields.Boolean('Is Available', compute='_compute_availability')

    @api.depends('make_id.name', 'model_id.name', 'year', 'color_exterior')
    def _compute_display_name(self):
        for car in self:
            name_parts = []
            if car.year:
                name_parts.append(str(car.year))
            if car.make_id:
                name_parts.append(car.make_id.name)
            if car.model_id:
                name_parts.append(car.model_id.name)
            if car.color_exterior:
                name_parts.append(f"({car.color_exterior})")
            car.display_name = ' '.join(name_parts) if name_parts else 'New Car'

    @api.onchange('product_id')
    def _onchange_product_id(self):
        if self.product_id:
            self.selling_price = self.product_id.list_price

    @api.depends('year')
    def _compute_age(self):
        current_year = date.today().year
        for car in self:
            car.age = current_year - car.year if car.year else 0

    @api.depends('date_acquired')
    def _compute_days_in_inventory(self):
        today = date.today()
        for car in self:
            if car.date_acquired:
                car.days_in_inventory = (today - car.date_acquired).days
            else:
                car.days_in_inventory = 0

    @api.depends('status')
    def _compute_availability(self):
        for car in self:
            car.is_available = car.status == 'available'

    def _create_product_description(self):
        """Generate a detailed product description"""
        self.ensure_one()
        description_parts = []

        # Basic vehicle info
        if self.year and self.make_id and self.model_id:
            description_parts.append(f"{self.year} {self.make_id.name} {self.model_id.name}")

        # Vehicle details
        details = []
        if self.mileage:
            details.append(f"Mileage: {self.mileage:,} km")
        if self.fuel_type:
            details.append(f"Fuel: {dict(self._fields['fuel_type'].selection).get(self.fuel_type)}")
        if self.transmission:
            details.append(f"Transmission: {dict(self._fields['transmission'].selection).get(self.transmission)}")
        if self.engine_size:
            details.append(f"Engine: {self.engine_size}L")
        if self.color_exterior:
            details.append(f"Color: {self.color_exterior}")

        if details:
            description_parts.append(" | ".join(details))

        # Condition
        if self.condition:
            condition_label = dict(self._fields['condition'].selection).get(self.condition)
            description_parts.append(f"Condition: {condition_label}")

        # Features
        if self.feature_ids:
            features = ", ".join(self.feature_ids.mapped('name'))
            description_parts.append(f"Features: {features}")

        # Custom description
        if self.description:
            description_parts.append(self.description)

        return "\n".join(description_parts)

    def _get_product_category(self):
        """Get or create product category for cars"""
        category = self.env['product.category'].search([('name', '=', 'Vehicles')], limit=1)
        if not category:
            category = self.env['product.category'].create({
                'name': 'Vehicles',
                'parent_id': False,
            })
        return category

    @api.model
    def create(self, vals):
        # Create the car record first
        car = super(Car, self).create(vals)

        # Create product automatically if not provided
        if not car.product_id:
            car._create_linked_product()

        return car

    def _create_linked_product(self):
        """Create a linked product for this car"""
        self.ensure_one()

        # Check if product already exists with this VIN
        existing_product = self.env['product.product'].search([
            ('default_code', '=', self.vin)
        ], limit=1)

        if existing_product:
            self.product_id = existing_product
            return existing_product

        # Create new product
        product_vals = {
            'name': self.display_name or 'Vehicle',
            'default_code': self.vin,
            'list_price': self.selling_price or 0.0,
            'standard_price': self.purchase_price or 0.0,
            'type': 'product',
            'categ_id': self._get_product_category().id,
            'image_1920': self.image_main,
            'description_sale': self._create_product_description(),
            'sale_ok': True,
            'purchase_ok': False,
            'tracking': 'serial',  # Since each car is unique
            'invoice_policy': 'order',
        }

        product = self.env['product.product'].create(product_vals)
        self.product_id = product

        return product

    def write(self, vals):
        """Update linked product when car is updated"""
        result = super(Car, self).write(vals)

        # Update product if relevant fields change
        update_product_fields = [
            'display_name', 'selling_price', 'purchase_price',
            'image_main', 'description', 'make_id', 'model_id',
            'year', 'color_exterior', 'mileage', 'fuel_type',
            'transmission', 'engine_size', 'condition', 'feature_ids'
        ]

        if any(field in vals for field in update_product_fields):
            for car in self:
                if car.product_id:
                    car._update_linked_product()

        return result

    def _update_linked_product(self):
        """Update the linked product with current car information"""
        self.ensure_one()
        if not self.product_id:
            return

        product_vals = {
            'name': self.display_name,
            'list_price': self.selling_price or 0.0,
            'standard_price': self.purchase_price or 0.0,
            'image_1920': self.image_main,
            'description_sale': self._create_product_description(),
        }

        self.product_id.write(product_vals)

    def action_view_service_history(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Service History',
            'view_mode': 'tree,form',
            'res_model': 'car.dealership.service',
            'domain': [('car_id', '=', self.id)],
            'context': {'default_car_id': self.id},
        }

    @api.onchange('make_id')
    def _onchange_make_id(self):
        if self.make_id:
            return {'domain': {'model_id': [('make_id', '=', self.make_id.id)]}}
        else:
            return {'domain': {'model_id': []}}

    @api.constrains('vin')
    def _check_vin_unique(self):
        for car in self:
            if car.vin:
                existing = self.search([('vin', '=', car.vin), ('id', '!=', car.id)])
                if existing:
                    raise ValidationError(f"VIN {car.vin} already exists in the system!")

    @api.constrains('year')
    def _check_year(self):
        current_year = date.today().year
        for car in self:
            if car.year and (car.year < 1900 or car.year > current_year + 1):
                raise ValidationError(f"Year must be between 1900 and {current_year + 1}")

    def action_reserve(self):
        self.status = 'reserved'

    def action_make_available(self):
        self.status = 'available'

    def action_mark_sold(self):
        self.ensure_one()
        product = self.product_id
        if not product:
            product = self._create_linked_product()

        partner = self.owner_id or self.env['res.partner'].search([('name', '=', 'Default Customer')], limit=1)
        if not partner:
            partner = self.env['res.partner'].create({'name': 'Default Customer'})

        sale_order = self.env['sale.order'].create({
            'partner_id': partner.id,
            'order_line': [(0, 0, {
                'product_id': product.id,
                'name': self.display_name,
                'price_unit': self.selling_price,
                'product_uom_qty': 1,
            })],
        })

        self.sale_order_id = sale_order.id
        self.status = 'sold'

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'sale.order',
            'res_id': sale_order.id,
            'view_mode': 'form',
        }

    def action_mark_leased(self):
        self.status = 'leased'
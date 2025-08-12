{
    'name': 'Car Dealership Management',
    'version': '18.0.1.0.0',
    'category': 'Sales/Inventory',
    'summary': 'Advanced Car Dealership Management System with Fleet Integration',
    'description': """
        Modern Car Dealership Management System for Odoo 18
        ===================================================

        This module provides comprehensive car dealership management with three business models:
        * Owner's Products: Direct inventory management
        * Dealer Network Products: Commission-based sales
        * Consigned Products: Third-party consignment sales

        Features:
        * Integration with Odoo 18 Fleet Management
        * Advanced vehicle tracking with VIN/Serial numbers
        * Automated accounting entries for all business scenarios
        * Commission management and profit tracking
        * Modern UI with enhanced reporting
        * Multi-location support

        Built for Odoo 18 with modern best practices.
    """,
    'author': 'Ayanfe - Mattobell',
    'website': 'https://mattobellonline.com/',
    'license': 'LGPL-3',
    'depends': [
        'base',
        'mail',
        'fleet',
        'stock',
        'purchase',
        'sale',  # Ensure sale is required
        'account',
        'product',
        'stock_account',  # Uncommented - this is usually needed
        'sale_stock',
        'account_invoice_extract',
        # Removed potentially problematic dependencies
        'partner_autocomplete',  # This might not be available in your setup
        # 'sale_pdf_quote_builder',  # This might be causing conflicts
    ],
    'data': [
        # Security
        # 'security/dealership_security.xml',
        'security/ir.model.access.csv',

        # Data
        'data/dealership_data.xml',
        'data/product_category_data.xml',
        'data/dealership_cron.xml',

        # Views
        'views/dealership_vehicle_views.xml',
        'views/dealership_dashboard_views.xml',
        'views/product_template_views.xml',
        'views/dealership_actions.xml',
        'views/stock_move_form_views.xml',
        'views/stock_lot_views.xml',
        'views/fleet_vehicle_views.xml',
        # 'views/dealership_product_views.xml',
        # 'views/dealership_purchase_views.xml',
        # 'views/dealership_sale_views.xml',
        # 'views/res_config_settings_views.xml',

        # Menus
        'views/dealership_menus.xml',

        # Reports
        'report/dealership_vehicle_report.xml',
        'security/dealership_vehicle_rule.xml',
    ],
    'demo': [
        'data/demo_dealership_vehicle.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'car_dealership/static/src/css/dealership_styles.css',
        ],
    },
    'installable': True,
    'auto_install': False,
    'application': True,
    'sequence': 95,
}

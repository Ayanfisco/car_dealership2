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
        'sale',
        'account',
        'mail',
        'fleet',
        'stock',
        'purchase',
        'product',
        'stock_account',
        'sale_stock',
        'base_import',
        'calendar',
    ],
    'data': [
        # Security
        'security/dealership_security.xml',
        'security/ir.model.access.csv',

        # Data
        'data/dealership_data.xml',
        'data/product_category_data.xml',
        'data/dealership_cron.xml',
        'data/fleet_vehicle_state_data.xml',
        # 'data/website_data.xml',

        # Backend Views
        'views/dealership_vehicle_views.xml',
        'views/product_template_views.xml',
        'views/fleet_vehicle_views.xml',
        'views/actions.xml',
        'views/dealership_menus.xml',

        # Website Templates
        # 'views/website/vehicle_templates.xml',
        # 'views/website/vehicle_detail.xml',
        #  'views/website/vehicle_snippets.xml',
        # 'views/website/vehicle_filters.xml',
        # 'views/website/vehicle_search.xml',
        # 'views/website/inquiry_form.xml',
        # 'views/website/test_drive_form.xml',

        # Website Menus and Pages
        # 'views/website/website_menus.xml',
        # 'views/website/website_pages.xml',

        # Reports
        'report/dealership_vehicle_report.xml',
    ],
    'demo': [
        'data/demo_dealership_vehicle.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'car_dealership/static/src/css/dealership_dashboard.css',
        ],
        'web.assets_frontend': [
            # CSS
            'car_dealership/static/src/css/vehicle_grid.css',
            'car_dealership/static/src/css/vehicle_detail.css',
            # JavaScript
            'car_dealership/static/src/js/website_dealership.js',
            'car_dealership/static/src/js/vehicle_gallery.js',
            'car_dealership/static/src/js/vehicle_filters.js',
            'car_dealership/static/src/js/inquiry_form.js',
            'car_dealership/static/src/js/test_drive.js',
        ],
        'website.assets_wysiwyg': [
            'car_dealership/static/src/snippets/snippets.js',
            'car_dealership/static/src/snippets/snippets.scss',
        ],
    },
    'installable': True,
    'auto_install': False,
    'application': True,
    'sequence': 95,
    # 'post_init_hook': 'check_sale_installed',
}

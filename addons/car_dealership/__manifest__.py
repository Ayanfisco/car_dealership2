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
        'fleet',
        'stock',
        'purchase',
        'sale',
        'account',
        'product',
        'stock_account',
        'partner_autocomplete',
        'sale_stock',
        'sale_pdf_quote_builder',
    ],
    'data': [
        # Security
        'security/dealership_security.xml',
        'security/ir.model.access.csv',

        # Data
        'data/dealership_data.xml',
        'data/product_category_data.xml',

        # Views
        'views/dealership_vehicle_views.xml',
        # 'views/dealership_product_views.xml',
        # 'views/dealership_purchase_views.xml',
        # 'views/dealership_sale_views.xml',
        # 'views/res_config_settings_views.xml',

        # Menus
        'views/dealership_menus.xml',
        #
        # # Reports
        # 'reports/dealership_reports.xml',
        # 'reports/profit_analysis_report.xml',
    ],
    # 'demo': [
    #     'demo/dealership_demo.xml',
    # ],
    # 'assets': {
    #     'web.assets_backend': [
    #         'car_dealership/static/src/css/dealership.css',
    #         'car_dealership/static/src/js/dealership_widgets.js',
    #     ],
    # },
    # 'images': ['static/description/banner.png'],
    'installable': True,
    'auto_install': False,
    'application': True,
    'sequence': 95,
}

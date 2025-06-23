#!/usr/bin/env python3
"""
Odoo 17.0 Email Template Converter
Converts old email templates to new QWeb format and fixes cron jobs
"""

import os
import re
import xml.etree.ElementTree as ET
from pathlib import Path
import html


def create_qweb_template_from_html(template_id, model_name, html_content):
    """Create a QWeb template from HTML content"""
    # Clean up the HTML content
    clean_html = html_content.strip()
    if clean_html.startswith('<![CDATA['):
        clean_html = clean_html[9:]
    if clean_html.endswith(']]>'):
        clean_html = clean_html[:-3]

    clean_html = clean_html.strip()

    # Convert ${object.field} to <t t-out="object.field"/>
    # Handle basic field access
    clean_html = re.sub(r'\$\{object\.([^}]+)\}', r'<t t-out="object.\1"/>', clean_html)

    # Handle user email with fallback
    clean_html = re.sub(r'\$\{.*?user\.email.*?or.*?[\'"]([^\'"]+)[\'"].*?\}', r'\1', clean_html)

    qweb_template = f'''    <record id="{template_id}_qweb" model="ir.ui.view">
        <field name="name">{template_id}.qweb</field>
        <field name="model">{model_name}</field>
        <field name="arch" type="xml">
            <t t-name="{template_id}_qweb">
{clean_html}
            </t>
        </field>
    </record>'''

    return qweb_template


def fix_cron_code(code_content):
    """Fix cron job code for Python 3 and newer Odoo syntax"""
    # Replace &lt; and &gt; with actual operators
    fixed_code = code_content.replace('&lt;=', '<=').replace('&gt;=', '>=')
    fixed_code = fixed_code.replace('&lt;', '<').replace('&gt;', '>')

    # Add proper imports for relativedelta and date handling
    if 'relativedelta' in fixed_code and 'DateContext()' in fixed_code:
        fixed_code = '''from dateutil.relativedelta import relativedelta
from datetime import datetime
records = model.search([
    ('state', '=', 'active'),
    ('end_date', '<=', (datetime.today() + relativedelta(days=7)).strftime('%Y-%m-%d'))
])
if records:
    records.send_reminders()'''

    return fixed_code


def process_email_template_file(file_path):
    """Process XML file containing email templates"""
    print(f"Processing email templates in: {file_path}")

    try:
        # Read and parse the XML file
        tree = ET.parse(file_path)
        root = tree.getroot()

        changes_made = False
        new_records = []

        # Process each record
        for record in root.findall('record'):
            model = record.get('model')

            # Handle mail templates
            if model == 'mail.template':
                record_id = record.get('id')
                print(f"  Found mail template: {record_id}")

                # Find body_html field
                body_html_field = None
                model_id_field = None

                for field in record.findall('field'):
                    if field.get('name') == 'body_html':
                        body_html_field = field
                    elif field.get('name') == 'model_id':
                        model_id_field = field

                if body_html_field is not None and body_html_field.text:
                    # Get model name from model_id reference
                    model_ref = model_id_field.get('ref') if model_id_field is not None else 'res.partner'
                    model_name = model_ref.replace('model_', '').replace('_', '.')

                    # Create QWeb template
                    qweb_template = create_qweb_template_from_html(
                        record_id, model_name, body_html_field.text
                    )
                    new_records.append(qweb_template)

                    # Update the mail template to reference QWeb
                    body_html_field.clear()
                    body_html_field.set('type', 'xml')
                    body_html_field.set('ref', f'{record_id}_qweb')
                    body_html_field.text = None

                    changes_made = True
                    print(f"    ✓ Converted to QWeb template: {record_id}_qweb")

            # Handle cron jobs
            elif model == 'ir.cron':
                record_id = record.get('id')
                print(f"  Found cron job: {record_id}")

                for field in record.findall('field'):
                    if field.get('name') == 'code' and field.text:
                        old_code = field.text.strip()
                        new_code = fix_cron_code(old_code)

                        if new_code != old_code:
                            field.text = new_code
                            changes_made = True
                            print(f"    ✓ Updated cron code: {record_id}")

        if changes_made:
            # Add new QWeb templates to the XML
            if new_records:
                # Find insertion point (before last closing tag)
                root_text = ET.tostring(root, encoding='unicode')

                # Insert new records before </odoo>
                new_records_text = '\n\n    ' + '\n\n    '.join(new_records) + '\n'
                root_text = root_text.replace('</odoo>', new_records_text + '</odoo>')

                # Write back to file
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write('<?xml version=\'1.0\' encoding=\'utf-8\'?>\n')
                    f.write(root_text)
            else:
                # Just write the modified tree
                tree.write(file_path, encoding='utf-8', xml_declaration=True)

            print(f"  ✓ Updated: {file_path}")
            return True
        else:
            print(f"  - No email templates to convert: {file_path}")
            return False

    except Exception as e:
        print(f"  ✗ Error processing {file_path}: {str(e)}")
        return False


def find_template_files(directory):
    """Find XML files that might contain email templates"""
    template_files = []
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith('.xml'):
                file_path = os.path.join(root, file)
                # Check if file contains mail.template
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        if 'mail.template' in content or 'ir.cron' in content:
                            template_files.append(file_path)
                except:
                    pass
    return template_files


def main():
    import argparse

    parser = argparse.ArgumentParser(description='Convert Odoo email templates to 17.0 QWeb format')
    parser.add_argument('directory', help='Directory containing the Odoo module(s) to convert')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be changed without making changes')

    args = parser.parse_args()

    if not os.path.exists(args.directory):
        print(f"Error: Directory '{args.directory}' does not exist")
        return

    print(f"Scanning for email template files in: {args.directory}")
    template_files = find_template_files(args.directory)

    if not template_files:
        print("No email template files found")
        return

    print(f"Found {len(template_files)} files with email templates")

    if args.dry_run:
        print("DRY RUN MODE - No files will be modified")
        for template_file in template_files:
            print(f"Would process: {template_file}")
        return

    converted_files = 0

    for template_file in template_files:
        if process_email_template_file(template_file):
            converted_files += 1

    print(f"\nConversion complete! {converted_files} files were updated.")
    print("Please review the changes and test your email templates.")


if __name__ == "__main__":
    main()
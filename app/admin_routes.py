from flask import Blueprint, flash, redirect, url_for
import os
import subprocess
import shutil
import logging

# Create the Blueprint for the admin section
admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/import_registries', methods=['POST'])
def import_registries():
    """
    Route to trigger the import of SQL files from the registries folder.
    """
    try:
        process_registry_files()
        flash('Registry import completed successfully!', 'success')
    except Exception as e:
        flash(f'Error importing registries: {e}', 'danger')
        logging.error(f"Error importing registries: {e}")

    return redirect(url_for('admin.admin_dashboard'))  # Redirect back to admin panel

def process_registry_files():
    """
    Process all SQL files in the immediate subfolders of the registries folder.
    """
    registries_dir = '/app/registries'  # Path where registries are stored in Docker

    for root, dirs, files in os.walk(registries_dir):
        if 'holding' in root:  # Skip already processed files in 'holding' folder
            continue

        for file in files:
            if file.endswith('.sql'):
                file_path = os.path.join(root, file)
                import_sql_file(file_path)
                move_to_holding(file_path, root)

def import_sql_file(file_path):
    """
    Import a single SQL file into the database, using the table name from the file name.
    """
    table_name = os.path.splitext(os.path.basename(file_path))[0]  # Get table name from file name

    # Construct the MySQL command to execute the SQL file
    cmd = [
        'mysql',
        '-u', os.getenv('DB_USER', 'airtrack_user'),  # Use environment variables for DB credentials
        '-p' + os.getenv('DB_PASSWORD', 'airtrack_pass'),  # Better to avoid exposing this in code
        os.getenv('DB_NAME', 'airtrack'),
        '--execute', f"source {file_path}"
    ]
    
    try:
        subprocess.run(cmd, check=True)
        logging.info(f"Successfully imported {file_path}")
    except subprocess.CalledProcessError as e:
        logging.error(f"Failed to import {file_path}: {e}")
        raise

def move_to_holding(file_path, root):
    """
    Move the processed SQL file to the holding directory within the respective country folder.
    """
    holding_folder = os.path.join(root, 'holding')

    # Ensure the holding folder exists
    if not os.path.exists(holding_folder):
        os.makedirs(holding_folder)

    # Move the file to the holding directory
    holding_path = os.path.join(holding_folder, os.path.basename(file_path))
    shutil.move(file_path, holding_path)
    logging.info(f"Moved {file_path} to {holding_path}")

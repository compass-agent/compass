import base64
import io
from PIL import Image
import numpy as np
from compass.database.models import Session, Template
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

def rescale_templates(inverse_x_scale: float = 1/0.8707482993197279, 
                     inverse_y_scale: float = 1/0.8368200836820083,
                     dry_run: bool = True):
    """
    Rescale all templates in the database using the inverse scaling factors
    
    Args:
        inverse_x_scale: The inverse of the x scaling factor used previously
        inverse_y_scale: The inverse of the y scaling factor used previously
        dry_run: If True, only show what would be done without making changes
    """
    try:
        with Session() as session:
            templates = session.query(Template).all()
            logger.info(f"Found {len(templates)} templates to process")
            
            # Create backup directory
            if not dry_run:
                backup_dir = Path(__file__).parent / 'template_backups'
                backup_dir.mkdir(exist_ok=True)
                
                # Backup current database
                import shutil
                db_path = Path(__file__).parent / 'template_database.db'
                backup_path = backup_dir / f'template_database_backup_{int(time.time())}.db'
                shutil.copy2(db_path, backup_path)
                logger.info(f"Created database backup at {backup_path}")

            for template in templates:
                try:
                    # Decode base64 image
                    img_bytes = base64.b64decode(template.base64_image)
                    img = Image.open(io.BytesIO(img_bytes))
                    
                    # Calculate new dimensions
                    new_width = round(img.width * inverse_x_scale)
                    new_height = round(img.height * inverse_y_scale)
                    
                    logger.info(f"Template '{template.caption}' - Original size: {img.width}x{img.height}, "
                              f"New size: {new_width}x{new_height}")
                    
                    if not dry_run:
                        # Resize image
                        resized_img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                        
                        # Convert back to base64
                        buffer = io.BytesIO()
                        resized_img.save(buffer, format='PNG', optimize=True)
                        new_base64 = base64.b64encode(buffer.getvalue()).decode()
                        
                        # Update database
                        template.base64_image = new_base64
                        
                except Exception as e:
                    logger.error(f"Error processing template {template.id} ({template.caption}): {e}")
                    continue
            
            if not dry_run:
                session.commit()
                logger.info("All templates have been rescaled and saved")
            else:
                logger.info("Dry run completed - no changes made")
                
    except Exception as e:
        logger.error(f"Error during template rescaling: {e}")
        raise

if __name__ == "__main__":
    import sys
    import time
    
    # Set up logging
    logging.basicConfig(level=logging.INFO)
    
    # Parse command line arguments
    dry_run = False
    if len(sys.argv) > 1 and sys.argv[1] == "--apply":
        dry_run = False
    
    print("Starting template rescaling process...")
    print(f"Mode: {'DRY RUN - no changes will be made' if dry_run else 'LIVE - changes will be applied'}")
    print("Using inverse scaling factors:")
    print(f"  X: {1/0.8707482993197279:.4f}")
    print(f"  Y: {1/0.8368200836820083:.4f}")
    
    if not dry_run:
        confirm = input("Are you sure you want to rescale all templates? This cannot be undone! (yes/no): ")
        if confirm.lower() != 'yes':
            print("Aborting...")
            sys.exit(0)
    
    rescale_templates(dry_run=dry_run)
    
    print("\nProcess completed!")
    if dry_run:
        print("To apply changes, run with --apply flag") 
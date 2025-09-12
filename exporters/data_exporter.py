import pandas as pd
import json
import csv
from typing import List, Dict, Any, Optional
from pathlib import Path
import logging
from datetime import datetime


class DataExporter:
    """Export scraped data to various formats with validation"""
    
    def __init__(self, output_dir: str = "output"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)
        
    def _generate_filename(self, base_name: str, extension: str) -> str:
        """Generate timestamped filename"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"{base_name}_{timestamp}.{extension}"
    
    def _validate_data(self, data: List[Dict[str, Any]]) -> bool:
        """Validate data before export"""
        if not data:
            self.logger.error("No data to export")
            return False
        
        if not isinstance(data, list):
            self.logger.error("Data must be a list of dictionaries")
            return False
        
        if not all(isinstance(item, dict) for item in data):
            self.logger.error("All data items must be dictionaries")
            return False
        
        return True
    
    def to_csv(self, data: List[Dict[str, Any]], filename: str = None) -> str:
        """Export data to CSV format"""
        if not self._validate_data(data):
            raise ValueError("Invalid data format")
        
        if filename is None:
            filename = self._generate_filename("catalog_data", "csv")
        
        filepath = self.output_dir / filename
        
        try:
            df = pd.DataFrame(data)
            
            # Ensure consistent column order
            desired_columns = [
                "Product Name", "Category", "SKU", "Variant/Strength",
                "Units/Size", "Core Price", "Premier Price", "Suggested Retail",
                "Bulk 10+", "Bulk 50+", "Bulk 100+", "Product URL"
            ]
            
            # Reorder columns if they exist
            available_columns = [col for col in desired_columns if col in df.columns]
            other_columns = [col for col in df.columns if col not in desired_columns]
            final_columns = available_columns + other_columns
            
            df = df[final_columns]
            
            # Export with UTF-8 encoding
            df.to_csv(filepath, index=False, encoding='utf-8-sig', quoting=csv.QUOTE_NONNUMERIC)
            
            self.logger.info(f"CSV exported successfully: {filepath}")
            return str(filepath)
            
        except Exception as e:
            self.logger.error(f"Error exporting to CSV: {str(e)}")
            raise
    
    def to_excel(self, data: List[Dict[str, Any]], filename: str = None) -> str:
        """Export data to Excel format with formatting"""
        if not self._validate_data(data):
            raise ValueError("Invalid data format")
        
        if filename is None:
            filename = self._generate_filename("catalog_data", "xlsx")
        
        filepath = self.output_dir / filename
        
        try:
            df = pd.DataFrame(data)
            
            # Ensure consistent column order
            desired_columns = [
                "Product Name", "Category", "SKU", "Variant/Strength",
                "Units/Size", "Core Price", "Premier Price", "Suggested Retail",
                "Bulk 10+", "Bulk 50+", "Bulk 100+", "Product URL"
            ]
            
            available_columns = [col for col in desired_columns if col in df.columns]
            other_columns = [col for col in df.columns if col not in desired_columns]
            final_columns = available_columns + other_columns
            
            df = df[final_columns]
            
            # Create Excel writer with formatting
            with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
                df.to_excel(writer, sheet_name='Product Catalog', index=False)
                
                # Get workbook and worksheet for formatting
                workbook = writer.book
                worksheet = writer.sheets['Product Catalog']
                
                # Auto-adjust column widths
                for column in worksheet.columns:
                    max_length = 0
                    column_letter = column[0].column_letter
                    
                    for cell in column:
                        try:
                            if len(str(cell.value)) > max_length:
                                max_length = len(str(cell.value))
                        except:
                            pass
                    
                    adjusted_width = min(max_length + 2, 50)  # Cap at 50 characters
                    worksheet.column_dimensions[column_letter].width = adjusted_width
                
                # Format header row
                from openpyxl.styles import Font, PatternFill, Alignment
                
                header_font = Font(bold=True, color="FFFFFF")
                header_fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
                header_alignment = Alignment(horizontal="center", vertical="center")
                
                for cell in worksheet[1]:
                    cell.font = header_font
                    cell.fill = header_fill
                    cell.alignment = header_alignment
            
            self.logger.info(f"Excel exported successfully: {filepath}")
            return str(filepath)
            
        except Exception as e:
            self.logger.error(f"Error exporting to Excel: {str(e)}")
            raise
    
    def to_json(self, data: List[Dict[str, Any]], filename: str = None) -> str:
        """Export data to JSON format"""
        if not self._validate_data(data):
            raise ValueError("Invalid data format")
        
        if filename is None:
            filename = self._generate_filename("catalog_data", "json")
        
        filepath = self.output_dir / filename
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"JSON exported successfully: {filepath}")
            return str(filepath)
            
        except Exception as e:
            self.logger.error(f"Error exporting to JSON: {str(e)}")
            raise
    
    def export_all_formats(self, data: List[Dict[str, Any]], base_filename: str = "catalog_data") -> Dict[str, str]:
        """Export data to all supported formats"""
        results = {}
        
        try:
            results['csv'] = self.to_csv(data, f"{base_filename}.csv")
            results['excel'] = self.to_excel(data, f"{base_filename}.xlsx")
            results['json'] = self.to_json(data, f"{base_filename}.json")
            
            self.logger.info("All formats exported successfully")
            return results
            
        except Exception as e:
            self.logger.error(f"Error during multi-format export: {str(e)}")
            raise
    
    def create_summary_report(self, data: List[Dict[str, Any]], validation_results: Dict[str, Any]) -> str:
        """Create a summary report of the scraping results"""
        report_filename = self._generate_filename("scraping_report", "txt")
        report_path = self.output_dir / report_filename
        
        try:
            with open(report_path, 'w', encoding='utf-8') as f:
                f.write("MOLAISONCRAWLER EXTRACTION REPORT\n")
                f.write("=" * 50 + "\n\n")
                
                f.write(f"Generation Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"Total Products Extracted: {len(data)}\n\n")
                
                if validation_results.get('success'):
                    f.write("EXTRACTION STATUS: SUCCESS ✓\n\n")
                    
                    f.write("FIELD COMPLETION RATES:\n")
                    f.write("-" * 30 + "\n")
                    
                    for field, rate in validation_results['field_completion_rates'].items():
                        status = "✓" if rate >= 80 else "⚠" if rate >= 50 else "✗"
                        f.write(f"{field:20} {rate:6.1f}% {status}\n")
                    
                    if validation_results.get('critical_fields_missing'):
                        f.write(f"\nCRITICAL FIELDS WITH LOW COMPLETION:\n")
                        for field in validation_results['critical_fields_missing']:
                            f.write(f"- {field}\n")
                else:
                    f.write("EXTRACTION STATUS: FAILED ✗\n")
                    f.write(f"Error: {validation_results.get('error', 'Unknown error')}\n")
                
                f.write("\nRECOMMENDations:\n")
                f.write("-" * 20 + "\n")
                
                completion_rates = validation_results.get('field_completion_rates', {})
                avg_completion = sum(completion_rates.values()) / len(completion_rates) if completion_rates else 0
                
                if avg_completion < 70:
                    f.write("- Review CSS selectors in configuration\n")
                    f.write("- Consider using Selenium for JavaScript-heavy sites\n")
                    f.write("- Check if authentication is required for full data access\n")
                elif avg_completion < 90:
                    f.write("- Fine-tune selectors for better precision\n")
                    f.write("- Validate against sample pages manually\n")
                else:
                    f.write("- Excellent extraction quality achieved!\n")
                    f.write("- Consider automating regular data updates\n")
            
            self.logger.info(f"Summary report created: {report_path}")
            return str(report_path)
            
        except Exception as e:
            self.logger.error(f"Error creating summary report: {str(e)}")
            raise
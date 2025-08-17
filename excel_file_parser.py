#!/usr/bin/env python3
"""
Robust Excel parser that can handle files with XML stylesheet issues
"""
import zipfile
import xml.etree.ElementTree as ET
import pandas as pd
import re
from pathlib import Path

class RobustExcelParser:
    def __init__(self):
        self.shared_strings = []
        self.cell_data = []
    
    def parse_excel_file(self, filepath):
        """Parse Excel file even if it has XML styling issues"""
        try:
            with zipfile.ZipFile(filepath, 'r') as z:
                # Step 1: Read shared strings
                self._parse_shared_strings(z)
                
                # Step 2: Read worksheet data
                self._parse_worksheet(z)
                
                # Step 3: Convert to DataFrame
                df = self._create_dataframe()
                
                return df
                
        except Exception as e:
            print(f"Error parsing {filepath}: {e}")
            return None
    
    def _parse_shared_strings(self, zip_file):
        """Extract shared strings from Excel file"""
        try:
            shared_strings_xml = zip_file.read('xl/sharedStrings.xml')
            
            # Parse XML properly
            root = ET.fromstring(shared_strings_xml)
            
            # Extract text values
            self.shared_strings = []
            for si in root.iter():
                if si.tag.endswith('t'):  # Text element
                    if si.text:
                        self.shared_strings.append(si.text)
            
            print(f"✅ Extracted {len(self.shared_strings)} shared strings")
            
        except Exception as e:
            print(f"⚠️ Could not parse shared strings: {e}")
            # Fallback: use regex
            try:
                xml_text = zip_file.read('xl/sharedStrings.xml').decode('utf-8', errors='ignore')
                self.shared_strings = re.findall(r'<t[^>]*>(.*?)</t>', xml_text)
                print(f"✅ Fallback extracted {len(self.shared_strings)} shared strings")
            except:
                self.shared_strings = []
    
    def _parse_worksheet(self, zip_file):
        """Extract cell data from worksheet"""
        try:
            # Try to parse XML properly first
            worksheet_xml = zip_file.read('xl/worksheets/sheet1.xml')
            
            try:
                root = ET.fromstring(worksheet_xml)
                self._parse_xml_cells(root)
            except ET.ParseError:
                # If XML parsing fails, use regex fallback
                print("⚠️ XML parsing failed, using regex fallback")
                self._parse_xml_regex(worksheet_xml)
                
        except Exception as e:
            print(f"Error parsing worksheet: {e}")
    
    def _parse_xml_cells(self, root):
        """Parse cells using proper XML parsing"""
        self.cell_data = []
        
        for row_elem in root.iter():
            if row_elem.tag.endswith('row'):
                row_data = {}
                row_num = int(row_elem.get('r', 0))
                
                for cell_elem in row_elem.iter():
                    if cell_elem.tag.endswith('c'):  # Cell element
                        cell_ref = cell_elem.get('r', '')
                        cell_type = cell_elem.get('t', '')
                        
                        # Get cell value
                        value_elem = cell_elem.find('.//{http://schemas.openxmlformats.org/spreadsheetml/2006/main}v')
                        if value_elem is not None and value_elem.text:
                            if cell_type == 's':  # Shared string
                                try:
                                    string_index = int(value_elem.text)
                                    if 0 <= string_index < len(self.shared_strings):
                                        cell_value = self.shared_strings[string_index]
                                    else:
                                        cell_value = value_elem.text
                                except:
                                    cell_value = value_elem.text
                            else:
                                cell_value = value_elem.text
                            
                            # Extract column from cell reference (A1 -> A, B1 -> B, etc.)
                            col_match = re.match(r'([A-Z]+)', cell_ref)
                            if col_match:
                                col = col_match.group(1)
                                row_data[col] = cell_value
                
                if row_data:
                    self.cell_data.append((row_num, row_data))
        
        print(f"✅ Extracted {len(self.cell_data)} rows of data")
    
    def _parse_xml_regex(self, xml_data):
        """Fallback regex parsing if XML is malformed"""
        xml_text = xml_data.decode('utf-8', errors='ignore')
        
        # Find all rows
        row_pattern = r'<row[^>]*r="(\d+)"[^>]*>(.*?)</row>'
        rows = re.findall(row_pattern, xml_text, re.DOTALL)
        
        self.cell_data = []
        
        for row_num, row_content in rows:
            row_data = {}
            
            # Find cells in this row
            cell_pattern = r'<c[^>]*r="([A-Z]+\d+)"[^>]*(?:t="([^"]*)")?[^>]*>.*?<v>(.*?)</v>'
            cells = re.findall(cell_pattern, row_content)
            
            for cell_ref, cell_type, value in cells:
                col_match = re.match(r'([A-Z]+)', cell_ref)
                if col_match:
                    col = col_match.group(1)
                    
                    if cell_type == 's':  # Shared string
                        try:
                            string_index = int(value)
                            if 0 <= string_index < len(self.shared_strings):
                                cell_value = self.shared_strings[string_index]
                            else:
                                cell_value = value
                        except:
                            cell_value = value
                    else:
                        cell_value = value
                    
                    row_data[col] = cell_value
            
            if row_data:
                self.cell_data.append((int(row_num), row_data))
        
        print(f"✅ Regex extracted {len(self.cell_data)} rows of data")
    
    def _create_dataframe(self):
        """Convert cell data to pandas DataFrame"""
        if not self.cell_data:
            return None
        
        # Sort by row number
        self.cell_data.sort(key=lambda x: x[0])
        
        # Get all columns that appear in the data
        all_cols = set()
        for row_num, row_data in self.cell_data:
            all_cols.update(row_data.keys())
        
        # Convert column letters to numbers for sorting (A=1, B=2, etc.)
        def col_to_num(col):
            result = 0
            for char in col:
                result = result * 26 + (ord(char) - ord('A') + 1)
            return result
        
        sorted_cols = sorted(all_cols, key=col_to_num)
        
        # Create matrix
        data_matrix = []
        for row_num, row_data in self.cell_data:
            row = [row_data.get(col, '') for col in sorted_cols]
            data_matrix.append(row)
        
        if not data_matrix:
            return None
        
        # Use first row as headers if they look like text
        if data_matrix and all(isinstance(cell, str) and not cell.replace('.', '').replace('-', '').isdigit() for cell in data_matrix[0] if cell):
            headers = data_matrix[0]
            data = data_matrix[1:]
        else:
            headers = [f'Column_{i}' for i in range(len(sorted_cols))]
            data = data_matrix
        
        # Create DataFrame
        df = pd.DataFrame(data, columns=headers)
        
        # Clean up empty rows and columns
        df = df.dropna(how='all').dropna(axis=1, how='all')
        
        print(f"✅ Created DataFrame with shape {df.shape}")
        print(f"📋 Columns: {list(df.columns)}")
        
        return df

def test_robust_parser():
    """Test the robust parser on both files"""
    parser = RobustExcelParser()
    
    files_to_test = [
        "_out/nvdr_20250817_124730.xlsx",
        "_out/short_sales_20250817_110455.xlsx"
    ]
    
    results = {}
    
    for filepath in files_to_test:
        if Path(filepath).exists():
            print(f"\n{'='*60}")
            print(f"Testing: {Path(filepath).name}")
            print('='*60)
            
            df = parser.parse_excel_file(filepath)
            results[filepath] = df
            
            if df is not None:
                print(f"🎉 Successfully parsed {Path(filepath).name}")
                print(f"📊 Final shape: {df.shape}")
                print("📝 Sample data:")
                print(df.head(3))
                
                # Save as CSV
                csv_path = filepath.replace('.xlsx', '_parsed.csv')
                df.to_csv(csv_path, index=False)
                print(f"💾 Saved as {csv_path}")
            else:
                print(f"❌ Failed to parse {Path(filepath).name}")
    
    return results

if __name__ == "__main__":
    results = test_robust_parser()
    
    print(f"\n{'='*60}")
    print("FINAL SUMMARY")
    print('='*60)
    
    for filepath, result in results.items():
        filename = Path(filepath).name
        if result is not None:
            print(f"✅ {filename}: {result.shape} - SUCCESSFULLY PARSED!")
        else:
            print(f"❌ {filename}: FAILED TO PARSE")
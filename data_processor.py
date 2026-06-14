"""
Data Processor Module
Handles loading and processing of car data from CSV/Excel files for the RAG pipeline.
"""

import pandas as pd
from typing import List, Dict, Any
import os


class DataProcessor:
    """Process car data from CSV/Excel files for RAG pipeline"""
    
    def __init__(self, data_path: str = "Cars Datasets 2025.csv"):
        """
        Initialize the data processor
        
        Args:
            data_path: Path to the car data file (CSV or Excel)
        """
        self.data_path = data_path
        self.df = None
        self.documents = []
        self.metadatas = []
        
    def load_data(self) -> pd.DataFrame:
        """
        Load car data from CSV or Excel file
        
        Returns:
            DataFrame containing car data
        """
        if not os.path.exists(self.data_path):
            raise FileNotFoundError(f"Data file not found: {self.data_path}")
        
        # Determine file type and load accordingly
        if self.data_path.endswith('.csv'):
            self.df = pd.read_csv(self.data_path, encoding='latin1')
        elif self.data_path.endswith(('.xlsx', '.xls')):
            self.df = pd.read_excel(self.data_path)
        else:
            raise ValueError("Unsupported file format. Use CSV or Excel.")
        
        print(f"📊 Loaded {len(self.df)} cars from {self.data_path}")
        return self.df
    
    def format_car_document(self, row: pd.Series) -> str:
        """
        Format a car's specifications into a natural language document
        
        Args:
            row: DataFrame row containing car specifications
            
        Returns:
            Formatted text document
        """
        doc = f"""The {row['Company Names']} {row['Cars Names']} features a {row['Engines']} engine with {row['CC/Battery Capacity']}, 
producing {row['HorsePower']} and {row['Torque']}. It achieves a top speed of {row['Total Speed']} with 
{row['Performance(0 - 100 )KM/H']} acceleration from 0-100 km/h. Priced at {row['Cars Prices']}, 
this {row['Fuel Types']} vehicle has {row['Seats']} seats."""
        return doc.strip()
    
    def create_metadata(self, row: pd.Series) -> Dict[str, Any]:
        """
        Create metadata for filtering and structured queries
        
        Args:
            row: DataFrame row containing car specifications
            
        Returns:
            Dictionary containing metadata
        """
        return {
            "company": row['Company Names'],
            "model": row['Cars Names'],
            "engine": row['Engines'],
            "cc_capacity": row['CC/Battery Capacity'],
            "horsepower": row['HorsePower'],
            "top_speed": row['Total Speed'],
            "acceleration": row['Performance(0 - 100 )KM/H'],
            "price": row['Cars Prices'],
            "fuel_type": row['Fuel Types'],
            "seats": row['Seats'],
            "torque": row['Torque']
        }
    
    def process_data(self) -> tuple[List[str], List[Dict[str, Any]]]:
        """
        Process the loaded data into documents and metadata
        
        Returns:
            Tuple of (documents list, metadatas list)
        """
        if self.df is None:
            self.load_data()
        
        self.documents = []
        self.metadatas = []
        
        for idx, row in self.df.iterrows():
            doc_text = self.format_car_document(row)
            metadata = self.create_metadata(row)
            
            self.documents.append(doc_text)
            self.metadatas.append(metadata)
        
        print(f"📝 Created {len(self.documents)} car documents")
        return self.documents, self.metadatas
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about the loaded data
        
        Returns:
            Dictionary containing data statistics
        """
        if self.df is None:
            self.load_data()
        
        stats = {
            "total_cars": len(self.df),
            "companies": self.df['Company Names'].nunique(),
            "fuel_types": self.df['Fuel Types'].unique().tolist(),
            "columns": list(self.df.columns)
        }
        
        return stats


if __name__ == "__main__":
    # Test the data processor
    processor = DataProcessor()
    processor.load_data()
    docs, metadatas = processor.process_data()
    stats = processor.get_statistics()
    
    print("\n📊 Data Statistics:")
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
    print("\n📝 Sample Document:")
    print(docs[0])
    
    print("\n🏷️ Sample Metadata:")
    print(metadatas[0])

import pandas as pd
import xml.etree.ElementTree as ET

""" This program compares the product data from Handicapmidler.dk with the scraped data from Mobilex.dk."""
def main():
    exported_df = get_product_data()
    mobilex_df = get_mobilex_data()

    print(f"{len(mobilex_df)} products found on Mobilex.dk")
    print(f"{len(exported_df)} products found in Handicapmidler.dk")

    """ List products that are in Mobilex but not in the export.xml file """
    missing_df = list_products_missing_in_export(mobilex_df, exported_df)
    missing_df.to_csv("productService/generated/products_missing_in_export.csv", index=False)

def list_products_missing_in_export(mobilex_df, exported_df):
    merged_df = mobilex_df.merge(exported_df, left_on='product_number', right_on='GENERAL_PROD_NUM', how='left', indicator=True)
    not_in_exported = merged_df[merged_df['_merge'] == 'left_only']
    return not_in_exported[['product_number', 'product_name', 'category_name', 'product_url']]

def filter_categories(df: pd.DataFrame) -> pd.DataFrame:
    spare_parts = [
        "Tilbehør rollatorer", "Reservedele rollatorer", "Reservedele/tilbehør til gangborde",
        "Reservedele/tilbehør til badestole", "Tilbehør til kørestole", "Reservedele til kørestole",
        "Rampetilbehør", "Eger og tilbehør", "Tilbehør til gummiramper"
    ]
    top_level_categories = [
        "Rollator", "Toilet og bad", "Kørestole", "Kørestolsramper",
        "Spinergy og specialhjul", "Dørtrinsramper"
    ]
    exclude_list = spare_parts + top_level_categories
    return df[~df["category_name"].isin(exclude_list)]

def get_mobilex_data(csv_file = "productService/generated/mobilex_products.csv") -> pd.DataFrame:
    df = pd.read_csv(csv_file, sep=';')
    df = filter_categories(df)
    df = df.drop_duplicates(subset=['product_number'])
    df = df.reset_index(drop=True)

    return df

def get_product_data(xml_file = 'productService/generated/export.xml') -> pd.DataFrame:
    # Parse the XML file
    tree = ET.parse(xml_file)
    root = tree.getroot()
    
    # List to store product data
    products = []
    
    # Process each product element
    for product in root.find('ELEMENTS').findall('PRODUCT'):
        product_data = {}
        
        # Extract data from each section
        for section in product:
            section_name = section.tag
            
            # Handle PRICES section specially due to nested PRICE elements
            if section_name == 'PRICES':
                for i, price in enumerate(section.findall('PRICE')):
                    for price_elem in price:
                        product_data[f"PRICE_{i+1}_{price_elem.tag}"] = price_elem.text
            # Handle PRODUCT_CATEGORIES specially if it has multiple categories
            #elif section_name == 'PRODUCT_CATEGORIES':
            #    categories = [cat.text for cat in section.findall('*')]
            #    product_data['PRODUCT_CATEGORIES'] = ';'.join(filter(None, categories))
            # Process all other sections
            else:
                for elem in section:
                    column_name = f"{section_name}_{elem.tag}"
                    product_data[column_name] = elem.text
        
        products.append(product_data)
    
    # Create DataFrame from the collected data
    return pd.DataFrame(products)


if __name__ == "__main__":
    main()
    
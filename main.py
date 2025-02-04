import os
from flask import Flask, request, jsonify
import pandas as pd

# Initialize Flask app
app = Flask(__name__)

# Load the CSV data into memory
def load_csv(file_path):
    try:
        return pd.read_csv(file_path)
    except Exception as e:
        print(f"Error loading CSV: {e}")
        return None

# Path to the CSV file
FILE_PATH = 'sample_flooring_products.csv'

# Load the flooring data
flooring_data = load_csv(FILE_PATH)
if flooring_data is None:
    raise FileNotFoundError(f"Could not find the file {FILE_PATH}. Ensure it is uploaded correctly.")

# Default route for health check
@app.route('/')
def index():
    return "Flooring Chatbot is running!"

# Webhook route for handling Dialogflow requests
@app.route('/webhook', methods=['POST'])
def webhook():
    try:
        # Parse the incoming JSON request
        req = request.get_json()
        intent_name = req['queryResult']['intent']['displayName']

        # Handle the 'list_flooring_options' intent
        if intent_name == 'list_flooring_types':
            types = flooring_data['Type'].unique()
            response = f"We offer the following flooring types: {', '.join(types)}."

        # Handle the 'product_pricing' intent
        elif intent_name == 'product_pricing':
            flooring_type = req['queryResult']['parameters'].get('flooring_type')
            product = flooring_data[flooring_data['Type'].str.lower() == flooring_type.lower()]
            if not product.empty:
                prices = product[['Product Name', 'Price per Sq Ft']].to_dict(orient='records')
                price_list = ', '.join([f"{p['Product Name']} - ${p['Price per Sq Ft']} per sq ft" for p in prices])
                response = f"The prices for {flooring_type} flooring are as follows: {price_list}."
            else:
                response = f"Sorry, we don't have any {flooring_type} flooring available."

                # Handle the 'installation_cost' intent
        elif intent_name == 'installation_cost':
            flooring_type = req['queryResult']['parameters'].get('flooring_type')
            product_name = req['queryResult']['parameters'].get('product_name')  # New parameter
            size = req['queryResult']['parameters'].get('number')  # Floor size

            if flooring_type and product_name and size:
                # Filter flooring data for the specified type and product name
                product = flooring_data[
                    (flooring_data['Type'].str.lower() == flooring_type.lower()) &
                    (flooring_data['Product Name'].str.lower() == product_name.lower())
                ]
                
                if not product.empty:
                    product = product.iloc[0]  # Take the first match
                    price_per_sq_ft = product['Price per Sq Ft']
                    install_cost_per_sq_ft = product['Installation Cost per Sq Ft']

                    # Calculate costs
                    total_material_cost = price_per_sq_ft * size
                    total_install_cost = install_cost_per_sq_ft * size
                    if size < 1000:
                        total_install_cost += 250  # Minimum fee for small areas
                    
                    total_cost = total_material_cost + total_install_cost
                    response = (
                        f"The total cost to install {size} sq ft of {product_name} ({flooring_type}) flooring is "
                        f"${total_cost:.2f}."
                    )
                else:
                    response = f"Sorry, we don't have information on the product {product_name} under {flooring_type} flooring."
            else:
                response = "Please specify the flooring type, product name, and area size for installation."

            return jsonify({"fulfillmentText": response})

        # Handle the 'list_product_names' intent
        elif intent_name == 'list_product_names':
            flooring_type = req['queryResult']['parameters'].get('flooring_type')
            if flooring_type:
                # Filter products based on the specified flooring type
                products = flooring_data[flooring_data['Type'].str.lower() == flooring_type.lower()]
                if not products.empty:
                    product_names = products['Product Name'].unique()
                    response = f"The available {flooring_type} products are: {', '.join(product_names)}."
                else:
                    response = f"Sorry, we don't have any products under the {flooring_type} type."
            else:
                response = "Please specify a flooring type to get the product names."
            return jsonify({"fulfillmentText": response})


        else:
            response = "Please specify the type of flooring and the area size for installation."

        return jsonify({"fulfillmentText": response})


    except Exception as e:
        print(f"Error processing request: {e}")
        return jsonify({"fulfillmentText": "Something went wrong. Please try again later."})

# Run the app
if __name__ == '__main__':
    # Use the PORT environment variable for Replit
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)

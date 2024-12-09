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
        if intent_name == 'list_flooring_options':
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
            size = req['queryResult']['parameters'].get('floor_size')
            product = flooring_data[flooring_data['Type'].str.lower() == flooring_type.lower()]
            if not product.empty:
                product = product.iloc[0]  # Take the first match
                price_per_sq_ft = product['Price per Sq Ft']
                install_cost_per_sq_ft = product['Installation Cost per Sq Ft']
                total_material_cost = price_per_sq_ft * size
                total_install_cost = install_cost_per_sq_ft * size
                if size < 1000:
                    total_install_cost += 250  # Minimum fee for small areas
                total_cost = total_material_cost + total_install_cost
                response = f"The total cost to install {size} sq ft of {flooring_type} flooring is ${total_cost:.2f}."
            else:
                response = f"Sorry, we don't have information on {flooring_type} flooring."

        # Handle unrecognized intents
        else:
            response = "I'm sorry, I didn't understand that."

        # Return the response as JSON
        return jsonify({"fulfillmentText": response})

    except Exception as e:
        print(f"Error processing request: {e}")
        return jsonify({"fulfillmentText": "Something went wrong. Please try again later."})

# Run the app
if __name__ == '__main__':
    # Use the PORT environment variable for Replit
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)

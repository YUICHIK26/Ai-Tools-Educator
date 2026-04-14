# app/CheckModels.py
import requests
import json

def list_available_models(api_key):
    """List all available Cohere models using direct API call"""
    url = "https://api.cohere.ai/v1/models"
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        models_data = response.json()
        
        print("Available Cohere Models:")
        print("=" * 60)
        
        for model in models_data.get('models', []):
            print(f"Name: {model.get('name')}")
            print(f"  - Endpoint: {model.get('endpoint')}")
            print(f"  - Context Length: {model.get('context_length')}")
            if 'supported_features' in model:
                print(f"  - Features: {', '.join(model.get('supported_features', []))}")
            print("-" * 40)
            
        return models_data.get('models', [])
        
    except requests.exceptions.RequestException as e:
        print(f"API Error: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Response: {e.response.text}")
        return None

# Usage
if __name__ == "__main__":
    # Replace with your actual API key
    API_KEY = "YOUR_COHERE_API_KEY"  # Get from your .env file or config
    
    models = list_available_models(API_KEY)
    
    if models:
        print(f"\nTotal models available: {len(models)}")
        
        # Show chat models specifically
        chat_models = [model for model in models if model.get('endpoint') == 'chat']
        print(f"\nChat models: {len(chat_models)}")
        for model in chat_models:
            print(f"  - {model.get('name')}")
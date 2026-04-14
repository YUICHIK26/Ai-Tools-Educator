# fix_appopener.py:
import os
import shutil

def clear_appopener_cache():
    app_data_path = os.path.join(os.environ.get('LOCALAPPDATA', ''), 'AppOpener')
    
    if os.path.exists(app_data_path):
        try:
            shutil.rmtree(app_data_path)
            print(f"Successfully cleared AppOpener cache: {app_data_path}")
        except Exception as e:
            print(f"Error clearing cache: {e}")
    else:
        print("AppOpener cache folder not found.")
    
    print("Please restart your application.")

if __name__ == "__main__":
    clear_appopener_cache()
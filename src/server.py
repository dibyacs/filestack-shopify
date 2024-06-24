import uuid
import os
import json
import logging

from flask import Flask, redirect, request, render_template

import helpers
from shopify_client import ShopifyStoreClient
from filestack_client import FilestackClient
from models import DBConfig, db, ShopifyFilepicker

from dotenv import load_dotenv

load_dotenv()
WEBHOOK_APP_UNINSTALL_URL = os.environ.get('WEBHOOK_APP_UNINSTALL_URL')
print('webhook', WEBHOOK_APP_UNINSTALL_URL)


app = Flask(__name__)
app.config.from_object(DBConfig)
db.init_app(app)
with app.app_context():
    db.create_all()
    
fs_client = FilestackClient()


ACCESS_TOKEN = None
SHOP = None
FILESTACK_DEV_ID = None
FILESTACK_DEV_NAME = None
FILESTACK_EMAIL = None
NONCE = None
ACCESS_MODE = []  # Defaults to offline access mode if left blank or omitted. https://shopify.dev/apps/auth/oauth/access-modes
SCOPES = ['write_script_tags','write_products', 'write_files']  # https://shopify.dev/docs/admin-api/access-scopes

@app.template_filter('ensure_array')
def ensure_array(value):
    if value is None or value == '' or value == 'None':
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, str):
        if value.startswith('[') and value.endswith(']'):
            return json.loads(value)
        return [item.strip() for item in value.split(',')]
    return []

@app.template_filter('ensure_string')
def ensure_string(value):
    if value is None:
        return ''
    if isinstance(value, str):
        if value == 'None':
            return ''
        return value
    return ''

@app.template_filter('ensure_number')
def ensure_number(value):
    if value is None or value == 'None':
        return ''
    if isinstance(value, int):
        return value
    return ''

# bind default parameters to render_template
@app.context_processor
def inject_defaults():
    return {
        'SHOPIFY_API_KEY': os.environ.get('SHOPIFY_API_KEY'),
        'ENVIRONMENT': os.environ.get('ENVIRONMENT','PRODUCTION')
    }

@app.route('/app_launched', methods=['GET'])
@helpers.verify_web_call
def app_launched():  
    shop = request.args.get('shop')
    SHOP = shop
    global ACCESS_TOKEN, NONCE, FILESTACK_DEV_ID, FILESTACK_EMAIL
    
    if ACCESS_TOKEN:
        filepicker_info = ShopifyStoreClient.get_filepicker_config(ACCESS_TOKEN)
        if not filepicker_info:
            return render_template('filestack-login.html',shop=shop)
        else:
            return render_template('filestack-user-setting.html',filestack_obj=filepicker_info[0], title="Settings")

    # The NONCE is a single-use random value we send to Shopify so we know the next call from Shopify is valid (see #app_installed)
    #   https://en.wikipedia.org/wiki/Cryptographic_nonce
    NONCE = uuid.uuid4().hex
    redirect_url = helpers.generate_install_redirect_url(shop=shop, scopes=SCOPES, nonce=NONCE, access_mode=ACCESS_MODE)
    return redirect(redirect_url, code=302)


@app.route('/settings', methods=['GET'])
def settings():
    global SHOP, ACCESS_TOKEN
    
    if ACCESS_TOKEN:
        filepicker_info = ShopifyStoreClient.get_filepicker_config(ACCESS_TOKEN)
        return render_template('filestack-user-setting.html', filestack_obj=filepicker_info[0], title='Settings')
    
    return ""


@app.route('/reports-analysis', methods=['GET'])
def reports_analysis():
    global SHOP, ACCESS_TOKEN
    
    if ACCESS_TOKEN:
        filepicker_info = ShopifyStoreClient.get_filepicker_config(ACCESS_TOKEN)
        return render_template('filestack-report-analysis.html',filestack_obj=filepicker_info[0], title='Reports & Analytics')
    
    return ""


@app.route('/faqs', methods=['GET'])
def faqs():
    global SHOP, ACCESS_TOKEN
    
    if ACCESS_TOKEN:
        return render_template('filestack-faqs.html',shop=SHOP, title='FAQ')
    
    return ""


@app.route('/images', methods=['GET'])
def images():
    global SHOP, ACCESS_TOKEN
    if ACCESS_TOKEN:
        shopify_client = ShopifyStoreClient(shop=SHOP, access_token=ACCESS_TOKEN)
        product_list = shopify_client.get_all_products()
        shop_name = SHOP.replace(".myshopify.com", "")
        filepicker_info = ShopifyStoreClient.get_filepicker_config(ACCESS_TOKEN)
        return render_template('filestack-images.html',shop=SHOP,shop_name=shop_name,product_list=product_list['products'],filestack_obj=filepicker_info[0],title='Product Images')
    
    return ""

@app.route('/filepicker', methods=['GET'])
def filepicker():
    global SHOP, ACCESS_TOKEN
    if ACCESS_TOKEN:
        filepicker_info = ShopifyStoreClient.get_filepicker_config(ACCESS_TOKEN)
        return render_template('filestack-filepicker.html', filestack_obj=filepicker_info[0],title='Filepicker')
    
    return ""


@app.route('/app_installed', methods=['GET'])
@helpers.verify_web_call
def app_installed():
    state = request.args.get('state')
    global NONCE, ACCESS_TOKEN, SHOP

    # Shopify passes our NONCE, created in #app_launched, as the `state` parameter, we need to ensure it matches!
    if state != NONCE:
        return "Invalid `state` received", 400
    NONCE = None

    # Ok, NONCE matches, we can get rid of it now (a nonce, by definition, should only be used once)
    # Using the `code` received from Shopify we can now generate an access token that is specific to the specified `shop` with the
    #   ACCESS_MODE and SCOPES we asked for in #app_installed
    shop = request.args.get('shop')
    code = request.args.get('code')
    ACCESS_TOKEN = ShopifyStoreClient.authenticate(shop=shop, code=code)
    SHOP = shop

    # We have an access token! Now let's register a webhook so Shopify will notify us if/when the app gets uninstalled
    # NOTE This webhook will call the #app_uninstalled function defined below
    shopify_client = ShopifyStoreClient(shop=shop, access_token=ACCESS_TOKEN)
    shopify_client.create_webook(address=WEBHOOK_APP_UNINSTALL_URL, topic="app/uninstalled")

    redirect_url = helpers.generate_post_install_redirect_url(shop=shop)
    return redirect(redirect_url, code=302)


@app.route('/app_uninstalled', methods=['POST'])
@helpers.verify_webhook_call
def app_uninstalled():
    # https://shopify.dev/docs/admin-api/rest/reference/events/webhook?api[version]=2020-04
    # Someone uninstalled your app, clean up anything you need to
    # NOTE the shop ACCESS_TOKEN is now void!
    global ACCESS_TOKEN
    ACCESS_TOKEN = None

    webhook_topic = request.headers.get('X-Shopify-Topic')
    webhook_payload = request.get_json()
    #logging.error(f"webhook call received {webhook_topic}:\n{json.dumps(webhook_payload, indent=4)}")

    return "OK"


@app.route('/data_removal_request', methods=['POST'])
@helpers.verify_webhook_call
def data_removal_request():
    # https://shopify.dev/tutorials/add-gdpr-webhooks-to-your-app
    # Clear all personal information you may have stored about the specified shop
    return "OK"

@app.route('/upload-product-images', methods=['POST'])
def upload_product_image():
    image_url = request.form.get('image_url')
    product_id = request.form.get('product_id')
    shopify_client = ShopifyStoreClient(shop=SHOP, access_token=ACCESS_TOKEN)
    response = shopify_client._upload_product_image(image_url,product_id)
    
    if response:
        return {'msg':'Image uploaded','status':200}
    
    return {'msg':'Image not uploaded','status':400}


@app.route('/upload-image-file', methods=['POST'])
def upload_image_file():
    alt = request.form.get('alt')
    image_url = request.form.get('image_url')
    shopify_client = ShopifyStoreClient(shop=SHOP, access_token=ACCESS_TOKEN)
    response = shopify_client._upload_image_file( alt=alt, image_url=image_url)

    if response:
        return {'msg':'Image uploaded','status':200}
    
    return {'msg':'Image not uploaded','status':400}


@app.route('/auth/filestack', methods=['POST'])
def authenticate_filestack():
    global SHOP, FILESTACK_DEV_NAME, FILESTACK_DEV_ID, FILESTACK_EMAIL, ACCESS_TOKEN
    filestack_email = request.form.get('filestack_email')
    filestack_password = request.form.get('filestack_password')
    res = fs_client.filestack_login(filestack_email,filestack_password)
    try:
        if res['id']:
            FILESTACK_DEV_ID = res['id']
            FILESTACK_EMAIL = res['email']
            FILESTACK_DEV_NAME = res['name']
            app_details = fs_client.get_filestack_app_detail(FILESTACK_DEV_ID, FILESTACK_EMAIL)
            api_key = app_details['list'][0]['apikey']

            with app.app_context():
                new_record =ShopifyFilepicker(
                    access_token = ACCESS_TOKEN,
                    apikey = api_key,
                    developer_id = FILESTACK_DEV_ID,
                    filestack_email= FILESTACK_EMAIL,
                    shop_domain = SHOP,
                )
                db.session.add(new_record)
                db.session.commit()
            return {'status':True,'msg':'Authentication success'}
        else:
            return {'status':False,'msg':'Authentication failed'}
    except Exception as e:
        return {'status':False,'msg':f'Authentication failed:{str(e)}'}


@app.route('/save-picker-preference', methods=['POST'])
def save_picker_preference():
    global SHOP, ACCESS_TOKEN, FILESTACK_DEV_NAME, FILESTACK_DEV_ID, FILESTACK_EMAIL
    picker_preference = dict()
    picker_preference['access_token']= request.form.get('access_token',ACCESS_TOKEN)
    picker_preference['policy'] = request.form.get('policy')
    picker_preference['signature'] = request.form.get('signature')
    picker_preference['apikey'] = request.form.get('filestack_apikey')
    picker_preference['accept_file_types'] = request.form.get('accept_file')
    picker_preference['allow_manual_retry'] = True if request.form.get('allow_manual_retry') else False
    picker_preference['display_mode'] = request.form.get('display_mode')
    picker_preference['disable_transformer'] = True if request.form.get('disable_transformer') else False
    picker_preference['support_email'] = request.form.get('support_email')
    picker_preference['language'] = request.form.get('language')
   
    picker_preference['cloud_container'] = request.form.get('cloud_container')
    picker_preference['cloud_folder'] = request.form.get('cloud_folder')
    picker_preference['cloud_path'] = request.form.get('cloud_path')
    
    picker_preference['from_sources'] = json.dumps(request.form.getlist('from_sources[]'))
    picker_preference['max_image_dimension'] = request.form.get('max_image_dimension')
    picker_preference['image_dimension'] = request.form.get('image_dimension')
    picker_preference['image_editor'] = request.form.get('image_editor')
    
    transformation = request.form.getlist('transformation[]')
    picker_preference['transformation_crop'] = True if 'crop' in transformation else False
    picker_preference['transformation_resize'] = True if 'resize' in transformation else False
    picker_preference['transformation_rotate'] = True if 'rotate' in transformation else False
    
    upload_tag_keys = request.form.getlist('tag_key[]')
    upload_tag_values = request.form.getlist('tag_value[]')
    upload_tags = dict()
    
    for i in range(len(upload_tag_keys)):
        upload_tags[upload_tag_keys[i]] = upload_tag_values[i]
    picker_preference['upload_tags'] = json.dumps(upload_tags) if upload_tags else ''
    
    picker_preference['intergrity_check'] = True if request.form.get('intergrity_check') else False
    picker_preference['intelligent'] = True if request.form.get('intelligent') else False
    
    picker_preference['max_filesize'] = int(request.form.get('max_size'))
    picker_preference['max_files'] = int(request.form.get('max_files'))
    picker_preference['min_files'] = int(request.form.get('min_files')) 
    picker_preference['num_retry'] = int(request.form.get('num_retry'))
    picker_preference['num_concurrency'] = int(request.form.get('num_concurrency'))
    picker_preference['error_timeout'] = int(request.form.get('error_timeout'))
    picker_preference['chunk_size'] = int(request.form.get('chunk_size'))
    picker_preference['part_size'] = int(request.form.get('part_size'))
    picker_preference['progress_interval'] = int(request.form.get('progress_interval'))
    picker_preference['retry_factor'] = int(request.form.get('retry_factor'))
    picker_preference['retry_maxtime'] = int(request.form.get('retry_maxtime'))
    try:
        record = ShopifyStoreClient.update_record(app, ACCESS_TOKEN, picker_preference)
        return {'status':True,'msg':'Filepicker preference saved'}
    except Exception as e:
        return {'status':False,'msg':f'Something error!{str(e)}'}



if __name__ == '__main__':
    # Bind to PORT if defined, otherwise default to 5000.
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=True, host='0.0.0.0', port=port)

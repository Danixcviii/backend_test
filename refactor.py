"""
This code defines a AWS Lambda that uses others lambdas to get information about, 
the products offered by a vending machine (type of product 'I guess', available amound, width, etc.. (I guess again)),
using a user_id and a device_id.

I didn't have the opportunity to test the code,
so I might have some syntax erros or even worst errors along the way, I have tried my best, sorry. 
"""

import json
import boto3

"""
#########################
# Roles table           #
#########################
# Id    # Name          #
#########################
# 0     # ADMIN         #
# 1     # CLIENT        #
# 2     # TECHNICIAN    #
# 3     # REPLENISHER   #
#########################
"""

__ADMIN__ = 0
__CLIENT__ = 1
__TECHNICIAN__ = 2
__REPLENISHER__ = 3


def from_dynamoDB(table: str, key_name: str, _id: str, *, function_name: str = 'DA_DynamoDB_Read') -> dict:
    """it invokes a given AWS Lambda, using a table, a key_name and a given id.

    Args:
        table (str): the table on the dynamoDB service
        key_name (str): the search key name 
        _id (str): the id to be found
        function_name (str): the AWS lambda to be called.
    
    Returns:
        dict: the server response
    """
    invokeLambda = boto3.client('lambda', region_name='us-east-2')
    lambda_response = invokeLambda.invoke(
        FunctionName = function_name,
        InvocationType = 'RequestResponse', 
        Payload = json.dumps({
            "table": table,
            "key_name": key_name,
            "key_value":_id
        }))
    
    resp_str = lambda_response['Payload'].read()
    return json.loads(resp_str)


def get_user_on_dynamoDB(user_id: str) -> dict:
    """Given a user_id returns the user flag and a user entity obj.

    Args:
        user_id (str): user id in the system

    Returns:
        tuple[bool,dict]: A tuple continaing 2 values:
            - bool: flag representing user access authorization
            - dict: the user entity object, represented as a python dict.
    """
    flag, user_entity, *_ = from_dynamoDB('user', 'id', user_id)
    return flag, user_entity

def get_iot_device_on_dynamoDB(device_id: str) -> dict:
    """  Given a device_id it returns a device flag anbd a device entity obj.

    Args:
        device_id (str): device id in the system.
    
    Returns:
        tuple[bool,dict]: A tuple containg 2 values:
            - bool: flag representing the availability of the device.
            - dict: the device entity object, represented as a python dict.
    """
    flag_device, device, *_ = from_dynamoDB('iotDevice', 'id', device_id)
    return flag_device, device

def get_iot_device_products_on_dynamoDB(device_id: str) -> dict:
    """  Given a device_id it returns a device products flag and a device 
    products entity obj.

    Args:
        device_id (str): device id in the system.
    
    Returns:
        tuple[bool,dict]: A tuple containg 2 values:
            - bool: flag representing the existence of products within the device.
            - dict: the products entity, that represents the list of products available in the device.
    """
    flag_device_products, device_products, *_ = from_dynamoDB('iotDeviceProducts', 'deviceId', device_id)
    return flag_device_products, device_products

def get_product_on_dynamoDB(product_id: str) -> dict:
    """  Given a product_id it returns a product flag and a product entity obj.

    Args:
        product_id (str): product id in the system.
    
    Returns:
        tuple[bool,dict]: A tuple containg 2 values:
            - bool: flag representing the existence of the product
            - dict: the product entity object, represented as a python dict.
    """
    flag_product, product, *_ = from_dynamoDB('product', 'id', product_id)
    return flag_product, product
    
def build_response(code: int, msg: str) -> dict:
    """This builds a simple datapayload to use on the response for an http request,
     given a code and a msg to show.

     Args:
        code (int): the HTTP code to return.
        msg (str): the message to show
     
     Returns:
        dict: a dict with the status code and message within the body.
        

    """
    return {
        'statusCode': code,
        'body': {
            'msg': msg
        }
    }

def lambda_handler(event: dict, context: dict) -> dict:

    """This function describes a AWS lambda that uses and userId and a deviceID,
    to check for the products offerend by a givin device, then it returns HTTP response,
    showing code and msg.
    
    Args:
        event (dict): params pushed to the AWS API.
        context (dict): other info passed by AWS.
    
    Returns:
        dict: the server response, with a list of products.
    """
    
    flag, user_entity = get_user_on_dynamoDB(event['userId'])
    if (not flag) or (not user_entity):
        return build_response(500, 'Unable to retrive user')
    flag = any([(role == __CLIENT__ or role == __REPLENISHER__) for role in user_entity['roles'] ])

    if not flag:
        return build_response(500, 'Unauthorized access')
    
    flag_device, device = get_iot_device_on_dynamoDB(event['deviceId'])

    if (not flag_device) or (not device):
        return build_response(500, 'Unable to get device')
    
    flag_device_products, device_products = get_iot_device_products_on_dynamoDB(event['deviceId'])
    
    if (not flag_device_products) or (not device_products):
        return build_response(500, 'Unable to get device products')
    
    products = []
    for device_product in device_products:
        flag_product, product = get_product_on_dynamoDB(device_product['productId'])
        if (not flag_product) or (not product):
            return build_response(500, 'Unable to get whole products')
        product['amount'] = device_product['amount']
        products.append(product)

    return {
        'statusCode': 200,
        'body': {
            'products': products,
            'widths': [p['width'] for p in products]
        }
    }
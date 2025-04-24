"""
This code defines a AWS Lambda that uses others lambdas to get information about, 
the products offered by a vending machine (type of product 'I guess', available amound, width, etc.. (I guess again)),
using a user_id and a device_id.

I didn't have the opportunity to test the code,
so I might have some syntax erros along the way, I tried my best, sorry. 
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

def get_user_on_dynamoDB(id):
    """ This function takes an user id and returns user information
    found on a DynamoDB service using the user table.
    """
    # all function returns a tuple, but the first value is a boolean,
    # for simplicity i am not mentioning on the docstring of the function, if it is ok :).
    invokeLambda = boto3.client('lambda', region_name='us-east-2')
    lambda_response = invokeLambda.invoke(FunctionName = 'DA_DynamoDB_Read', InvocationType = 'RequestResponse', 
        Payload = json.dumps({
            "table":"user",
            "key_name":"id",
            "key_value":id
        }))
    resp_str = lambda_response['Payload'].read()
    resp = json.loads(resp_str)
    return resp[0], resp[1]

def get_iot_device_on_dynamoDB(id):
    """ This function takes an device id and returns a device information
    found on the same service than the last function, but in the iotDevice table.  
    """
    invokeLambda = boto3.client('lambda', region_name='us-east-2')
    lambda_response = invokeLambda.invoke(FunctionName = 'DA_DynamoDB_Read', InvocationType = 'RequestResponse', 
        Payload = json.dumps({
            "table":"iotDevice",
            "key_name":"id",
            "key_value":id
        }))
    resp_str = lambda_response['Payload'].read()
    resp = json.loads(resp_str)
    return resp[0], resp[1]
    
def get_iot_device_on_dynamoDB(id):
    """ This function is duplicated, in name and in functionality.
    """
    invokeLambda = boto3.client('lambda', region_name='us-east-2')
    lambda_response = invokeLambda.invoke(FunctionName = 'DA_DynamoDB_Read', InvocationType = 'RequestResponse', 
        Payload = json.dumps({
            "table":"iotDevice",
            "key_name":"id",
            "key_value":id
        }))
    resp_str = lambda_response['Payload'].read()
    resp = json.loads(resp_str)
    return resp[0], resp[1]

def get_iot_device_products_on_dynamoDB(deviceId):
    """ This function returns a list of products asosiated with a given iotDevice,
     found in the same dynamoDb service using a deviceid and iotDeviceProducts table.
    """
    # all function returns a tuple, but the first value is a boolean,
    # for simplicity i am not mentioning on the docstring of the function, if it is ok :).
    invokeLambda = boto3.client('lambda', region_name='us-east-2')
    lambda_response = invokeLambda.invoke(FunctionName = 'DA_DynamoDB_Read', InvocationType = 'RequestResponse', 
        Payload = json.dumps({
            "table":"iotDeviceProducts",
            "key_name":"deviceId",
            "key_value":deviceId
        }))
    resp_str = lambda_response['Payload'].read()
    resp = json.loads(resp_str)
    return resp[0], resp[1]

def get_product_on_dynamoDB(id):
    """ this returns a product information found on the same dynamoDB service but in product table, using a product id.
    """
    invokeLambda = boto3.client('lambda', region_name='us-east-2')
    lambda_response = invokeLambda.invoke(FunctionName = 'DA_DynamoDB_Read', InvocationType = 'RequestResponse', 
        Payload = json.dumps({
            "table":"product",
            "key_name":"id",
            "key_value":id
        }))
    resp_str = lambda_response['Payload'].read()
    resp = json.loads(resp_str)
    return resp[0], resp[1]

def lambda_handler(event, context):
    """This is the AWS Lambda handler
        In general on a nested-nested-nested if-else stmt, this is checking that the user is registered (found) on the system and is authorized to access a device (in general), 
        then checking that the device is on the system, then that the device has products, and then that the products exists on the database.
        finally, it extract information about the products in the device, like ammount, and width
    """
    flag, user_entity = get_user_on_dynamoDB(event["userId"])
    if flag and user_entity:
        flag = False
        for role in user_entity["roles"]:
            if role == 1:
                flag = True
            if role == 3:
                flag = True
        if flag:
            flag_device, device = get_iot_device_on_dynamoDB(event["deviceId"])
            if flag_device and device:
                flag_device_products, device_products = get_iot_device_products_on_dynamoDB(event["deviceId"])
                if flag_device_products and device_products:
                    products = []
                    for i in range(len(device_products)):
                        flagProduct, product = get_product_on_dynamoDB(device_products[i]["productId"])
                        if flagProduct and product:
                            products.append(product)
                        else:
                            return {
                                'statusCode': 500,
                                'body': {
                                    'msg': "Unable to get whole products"
                                }
                            }
                    for i in range(len(products)):
                        product = products[i]
                        for j in range(len(device_products)):
                            if device_products[j]["productId"] == product["id"]:
                                product["amount"] = device_products[j]["amount"]
                        products[i] = product
                    products_width=[]
                    for i in range(len(products)):
                        products_width[i] = products[i]["width"]
                    return {
                        'statusCode': 200,
                        'body': {"products":list_products, "widths":products_width}
                    }
                else:
                    return {
                        'statusCode': 500,
                        'body': {
                            'msg': "Unable to get device products"
                        }
                    }
            else:
                return {
                    'statusCode': 500,
                    'body': {
                        'msg': "Unable to get device"
                    }
                }
        if not flag:
            return {
                'statusCode': 500,
                'body': {
                    'msg': "Unauthorized access"
                }
            }
    else:
        return {
            'statusCode': 500,
            'body': {
                'msg': "Unable to retrieve user"
            }
        }
    # This is a server error code.
    return {
        'statusCode': 500,
        'body': {
            'msg': "Unable to retrieve user"
        }
    }
        
            
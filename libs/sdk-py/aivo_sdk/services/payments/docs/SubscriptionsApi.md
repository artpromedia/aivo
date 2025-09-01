# aivo_sdk.SubscriptionsApi

All URIs are relative to *https://api.aivo.com/payments/v1*

Method | HTTP request | Description
------------- | ------------- | -------------
[**cancel_subscription**](SubscriptionsApi.md#cancel_subscription) | **POST** /subscriptions/{subscriptionId}/cancel | Cancel subscription
[**create_subscription**](SubscriptionsApi.md#create_subscription) | **POST** /subscriptions | Create new subscription
[**get_subscription**](SubscriptionsApi.md#get_subscription) | **GET** /subscriptions/{subscriptionId} | Get subscription by ID
[**list_subscriptions**](SubscriptionsApi.md#list_subscriptions) | **GET** /subscriptions | List subscriptions
[**update_subscription**](SubscriptionsApi.md#update_subscription) | **PUT** /subscriptions/{subscriptionId} | Update subscription


# **cancel_subscription**
> Subscription cancel_subscription(subscription_id, cancel_subscription_request=cancel_subscription_request)

Cancel subscription

### Example

* Bearer (JWT) Authentication (bearerAuth):

```python
import aivo_sdk
from aivo_sdk.models.cancel_subscription_request import CancelSubscriptionRequest
from aivo_sdk.models.subscription import Subscription
from aivo_sdk.rest import ApiException
from pprint import pprint

# Defining the host is optional and defaults to https://api.aivo.com/payments/v1
# See configuration.py for a list of all supported configuration parameters.
configuration = aivo_sdk.Configuration(
    host = "https://api.aivo.com/payments/v1"
)

# The client must configure the authentication and authorization parameters
# in accordance with the API server security policy.
# Examples for each auth method are provided below, use the example that
# satisfies your auth use case.

# Configure Bearer authorization (JWT): bearerAuth
configuration = aivo_sdk.Configuration(
    access_token = os.environ["BEARER_TOKEN"]
)

# Enter a context with an instance of the API client
with aivo_sdk.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = aivo_sdk.SubscriptionsApi(api_client)
    subscription_id = 'subscription_id_example' # str | 
    cancel_subscription_request = aivo_sdk.CancelSubscriptionRequest() # CancelSubscriptionRequest |  (optional)

    try:
        # Cancel subscription
        api_response = api_instance.cancel_subscription(subscription_id, cancel_subscription_request=cancel_subscription_request)
        print("The response of SubscriptionsApi->cancel_subscription:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling SubscriptionsApi->cancel_subscription: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **subscription_id** | **str**|  | 
 **cancel_subscription_request** | [**CancelSubscriptionRequest**](CancelSubscriptionRequest.md)|  | [optional] 

### Return type

[**Subscription**](Subscription.md)

### Authorization

[bearerAuth](../README.md#bearerAuth)

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | Subscription canceled successfully |  -  |
**400** | Bad request |  -  |
**401** | Unauthorized |  -  |
**404** | Subscription not found |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **create_subscription**
> Subscription create_subscription(create_subscription_request)

Create new subscription

### Example

* Bearer (JWT) Authentication (bearerAuth):

```python
import aivo_sdk
from aivo_sdk.models.create_subscription_request import CreateSubscriptionRequest
from aivo_sdk.models.subscription import Subscription
from aivo_sdk.rest import ApiException
from pprint import pprint

# Defining the host is optional and defaults to https://api.aivo.com/payments/v1
# See configuration.py for a list of all supported configuration parameters.
configuration = aivo_sdk.Configuration(
    host = "https://api.aivo.com/payments/v1"
)

# The client must configure the authentication and authorization parameters
# in accordance with the API server security policy.
# Examples for each auth method are provided below, use the example that
# satisfies your auth use case.

# Configure Bearer authorization (JWT): bearerAuth
configuration = aivo_sdk.Configuration(
    access_token = os.environ["BEARER_TOKEN"]
)

# Enter a context with an instance of the API client
with aivo_sdk.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = aivo_sdk.SubscriptionsApi(api_client)
    create_subscription_request = aivo_sdk.CreateSubscriptionRequest() # CreateSubscriptionRequest | 

    try:
        # Create new subscription
        api_response = api_instance.create_subscription(create_subscription_request)
        print("The response of SubscriptionsApi->create_subscription:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling SubscriptionsApi->create_subscription: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **create_subscription_request** | [**CreateSubscriptionRequest**](CreateSubscriptionRequest.md)|  | 

### Return type

[**Subscription**](Subscription.md)

### Authorization

[bearerAuth](../README.md#bearerAuth)

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**201** | Subscription created successfully |  -  |
**400** | Bad request |  -  |
**401** | Unauthorized |  -  |
**422** | Validation error |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **get_subscription**
> Subscription get_subscription(subscription_id)

Get subscription by ID

### Example

* Bearer (JWT) Authentication (bearerAuth):

```python
import aivo_sdk
from aivo_sdk.models.subscription import Subscription
from aivo_sdk.rest import ApiException
from pprint import pprint

# Defining the host is optional and defaults to https://api.aivo.com/payments/v1
# See configuration.py for a list of all supported configuration parameters.
configuration = aivo_sdk.Configuration(
    host = "https://api.aivo.com/payments/v1"
)

# The client must configure the authentication and authorization parameters
# in accordance with the API server security policy.
# Examples for each auth method are provided below, use the example that
# satisfies your auth use case.

# Configure Bearer authorization (JWT): bearerAuth
configuration = aivo_sdk.Configuration(
    access_token = os.environ["BEARER_TOKEN"]
)

# Enter a context with an instance of the API client
with aivo_sdk.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = aivo_sdk.SubscriptionsApi(api_client)
    subscription_id = 'subscription_id_example' # str | 

    try:
        # Get subscription by ID
        api_response = api_instance.get_subscription(subscription_id)
        print("The response of SubscriptionsApi->get_subscription:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling SubscriptionsApi->get_subscription: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **subscription_id** | **str**|  | 

### Return type

[**Subscription**](Subscription.md)

### Authorization

[bearerAuth](../README.md#bearerAuth)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | Subscription retrieved successfully |  -  |
**401** | Unauthorized |  -  |
**404** | Subscription not found |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **list_subscriptions**
> ListSubscriptions200Response list_subscriptions(tenant_id=tenant_id, status=status, limit=limit, offset=offset)

List subscriptions

### Example

* Bearer (JWT) Authentication (bearerAuth):

```python
import aivo_sdk
from aivo_sdk.models.list_subscriptions200_response import ListSubscriptions200Response
from aivo_sdk.rest import ApiException
from pprint import pprint

# Defining the host is optional and defaults to https://api.aivo.com/payments/v1
# See configuration.py for a list of all supported configuration parameters.
configuration = aivo_sdk.Configuration(
    host = "https://api.aivo.com/payments/v1"
)

# The client must configure the authentication and authorization parameters
# in accordance with the API server security policy.
# Examples for each auth method are provided below, use the example that
# satisfies your auth use case.

# Configure Bearer authorization (JWT): bearerAuth
configuration = aivo_sdk.Configuration(
    access_token = os.environ["BEARER_TOKEN"]
)

# Enter a context with an instance of the API client
with aivo_sdk.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = aivo_sdk.SubscriptionsApi(api_client)
    tenant_id = 'tenant_id_example' # str |  (optional)
    status = 'status_example' # str |  (optional)
    limit = 20 # int |  (optional) (default to 20)
    offset = 0 # int |  (optional) (default to 0)

    try:
        # List subscriptions
        api_response = api_instance.list_subscriptions(tenant_id=tenant_id, status=status, limit=limit, offset=offset)
        print("The response of SubscriptionsApi->list_subscriptions:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling SubscriptionsApi->list_subscriptions: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **tenant_id** | **str**|  | [optional] 
 **status** | **str**|  | [optional] 
 **limit** | **int**|  | [optional] [default to 20]
 **offset** | **int**|  | [optional] [default to 0]

### Return type

[**ListSubscriptions200Response**](ListSubscriptions200Response.md)

### Authorization

[bearerAuth](../README.md#bearerAuth)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | Subscriptions retrieved successfully |  -  |
**401** | Unauthorized |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **update_subscription**
> Subscription update_subscription(subscription_id, update_subscription_request)

Update subscription

### Example

* Bearer (JWT) Authentication (bearerAuth):

```python
import aivo_sdk
from aivo_sdk.models.subscription import Subscription
from aivo_sdk.models.update_subscription_request import UpdateSubscriptionRequest
from aivo_sdk.rest import ApiException
from pprint import pprint

# Defining the host is optional and defaults to https://api.aivo.com/payments/v1
# See configuration.py for a list of all supported configuration parameters.
configuration = aivo_sdk.Configuration(
    host = "https://api.aivo.com/payments/v1"
)

# The client must configure the authentication and authorization parameters
# in accordance with the API server security policy.
# Examples for each auth method are provided below, use the example that
# satisfies your auth use case.

# Configure Bearer authorization (JWT): bearerAuth
configuration = aivo_sdk.Configuration(
    access_token = os.environ["BEARER_TOKEN"]
)

# Enter a context with an instance of the API client
with aivo_sdk.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = aivo_sdk.SubscriptionsApi(api_client)
    subscription_id = 'subscription_id_example' # str | 
    update_subscription_request = aivo_sdk.UpdateSubscriptionRequest() # UpdateSubscriptionRequest | 

    try:
        # Update subscription
        api_response = api_instance.update_subscription(subscription_id, update_subscription_request)
        print("The response of SubscriptionsApi->update_subscription:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling SubscriptionsApi->update_subscription: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **subscription_id** | **str**|  | 
 **update_subscription_request** | [**UpdateSubscriptionRequest**](UpdateSubscriptionRequest.md)|  | 

### Return type

[**Subscription**](Subscription.md)

### Authorization

[bearerAuth](../README.md#bearerAuth)

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | Subscription updated successfully |  -  |
**400** | Bad request |  -  |
**401** | Unauthorized |  -  |
**404** | Subscription not found |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)


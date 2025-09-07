# aivo_sdk.LearnersApi

All URIs are relative to *<https://api.aivo.com/learner/v1>*

Method | HTTP request | Description
------------- | ------------- | -------------
[**create_learner**](LearnersApi.md#create_learner) | **POST** /learners | Create new learner
[**delete_learner**](LearnersApi.md#delete_learner) | **DELETE** /learners/{learnerId} | Delete learner
[**get_learner**](LearnersApi.md#get_learner) | **GET** /learners/{learnerId} | Get learner by ID
[**list_learners**](LearnersApi.md#list_learners) | **GET** /learners | List learners
[**update_learner**](LearnersApi.md#update_learner) | **PUT** /learners/{learnerId} | Update learner

# **create_learner**
>
> Learner create_learner(create_learner_request)

Create new learner

### Example

* Bearer (JWT) Authentication (bearerAuth):

```python
import aivo_sdk
from aivo_sdk.models.create_learner_request import CreateLearnerRequest
from aivo_sdk.models.learner import Learner
from aivo_sdk.rest import ApiException
from pprint import pprint

# Defining the host is optional and defaults to https://api.aivo.com/learner/v1
# See configuration.py for a list of all supported configuration parameters.
configuration = aivo_sdk.Configuration(
    host = "https://api.aivo.com/learner/v1"
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
    api_instance = aivo_sdk.LearnersApi(api_client)
    create_learner_request = aivo_sdk.CreateLearnerRequest() # CreateLearnerRequest | 

    try:
        # Create new learner
        api_response = api_instance.create_learner(create_learner_request)
        print("The response of LearnersApi->create_learner:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling LearnersApi->create_learner: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **create_learner_request** | [**CreateLearnerRequest**](CreateLearnerRequest.md)|  |

### Return type

[**Learner**](Learner.md)

### Authorization

[bearerAuth](../README.md#bearerAuth)

### HTTP request headers

* **Content-Type**: application/json
* **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**201** | Learner created successfully |  -  |
**400** | Bad request |  -  |
**401** | Unauthorized |  -  |
**409** | Learner already exists |  -  |
**422** | Validation error |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **delete_learner**
>
> delete_learner(learner_id)

Delete learner

### Example

* Bearer (JWT) Authentication (bearerAuth):

```python
import aivo_sdk
from aivo_sdk.rest import ApiException
from pprint import pprint

# Defining the host is optional and defaults to https://api.aivo.com/learner/v1
# See configuration.py for a list of all supported configuration parameters.
configuration = aivo_sdk.Configuration(
    host = "https://api.aivo.com/learner/v1"
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
    api_instance = aivo_sdk.LearnersApi(api_client)
    learner_id = 'learner_id_example' # str | 

    try:
        # Delete learner
        api_instance.delete_learner(learner_id)
    except Exception as e:
        print("Exception when calling LearnersApi->delete_learner: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **learner_id** | **str**|  |

### Return type

void (empty response body)

### Authorization

[bearerAuth](../README.md#bearerAuth)

### HTTP request headers

* **Content-Type**: Not defined
* **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**204** | Learner deleted successfully |  -  |
**401** | Unauthorized |  -  |
**404** | Learner not found |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **get_learner**
>
> Learner get_learner(learner_id)

Get learner by ID

### Example

* Bearer (JWT) Authentication (bearerAuth):

```python
import aivo_sdk
from aivo_sdk.models.learner import Learner
from aivo_sdk.rest import ApiException
from pprint import pprint

# Defining the host is optional and defaults to https://api.aivo.com/learner/v1
# See configuration.py for a list of all supported configuration parameters.
configuration = aivo_sdk.Configuration(
    host = "https://api.aivo.com/learner/v1"
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
    api_instance = aivo_sdk.LearnersApi(api_client)
    learner_id = 'learner_id_example' # str | 

    try:
        # Get learner by ID
        api_response = api_instance.get_learner(learner_id)
        print("The response of LearnersApi->get_learner:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling LearnersApi->get_learner: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **learner_id** | **str**|  |

### Return type

[**Learner**](Learner.md)

### Authorization

[bearerAuth](../README.md#bearerAuth)

### HTTP request headers

* **Content-Type**: Not defined
* **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | Learner retrieved successfully |  -  |
**401** | Unauthorized |  -  |
**404** | Learner not found |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **list_learners**
>
> ListLearners200Response list_learners(tenant_id, status=status, search=search, limit=limit, offset=offset)

List learners

### Example

* Bearer (JWT) Authentication (bearerAuth):

```python
import aivo_sdk
from aivo_sdk.models.list_learners200_response import ListLearners200Response
from aivo_sdk.rest import ApiException
from pprint import pprint

# Defining the host is optional and defaults to https://api.aivo.com/learner/v1
# See configuration.py for a list of all supported configuration parameters.
configuration = aivo_sdk.Configuration(
    host = "https://api.aivo.com/learner/v1"
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
    api_instance = aivo_sdk.LearnersApi(api_client)
    tenant_id = 'tenant_id_example' # str | 
    status = 'status_example' # str |  (optional)
    search = 'search_example' # str |  (optional)
    limit = 20 # int |  (optional) (default to 20)
    offset = 0 # int |  (optional) (default to 0)

    try:
        # List learners
        api_response = api_instance.list_learners(tenant_id, status=status, search=search, limit=limit, offset=offset)
        print("The response of LearnersApi->list_learners:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling LearnersApi->list_learners: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **tenant_id** | **str**|  |
 **status** | **str**|  | [optional]
 **search** | **str**|  | [optional]
 **limit** | **int**|  | [optional] [default to 20]
 **offset** | **int**|  | [optional] [default to 0]

### Return type

[**ListLearners200Response**](ListLearners200Response.md)

### Authorization

[bearerAuth](../README.md#bearerAuth)

### HTTP request headers

* **Content-Type**: Not defined
* **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | Learners retrieved successfully |  -  |
**401** | Unauthorized |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **update_learner**
>
> Learner update_learner(learner_id, update_learner_request)

Update learner

### Example

* Bearer (JWT) Authentication (bearerAuth):

```python
import aivo_sdk
from aivo_sdk.models.learner import Learner
from aivo_sdk.models.update_learner_request import UpdateLearnerRequest
from aivo_sdk.rest import ApiException
from pprint import pprint

# Defining the host is optional and defaults to https://api.aivo.com/learner/v1
# See configuration.py for a list of all supported configuration parameters.
configuration = aivo_sdk.Configuration(
    host = "https://api.aivo.com/learner/v1"
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
    api_instance = aivo_sdk.LearnersApi(api_client)
    learner_id = 'learner_id_example' # str | 
    update_learner_request = aivo_sdk.UpdateLearnerRequest() # UpdateLearnerRequest | 

    try:
        # Update learner
        api_response = api_instance.update_learner(learner_id, update_learner_request)
        print("The response of LearnersApi->update_learner:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling LearnersApi->update_learner: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **learner_id** | **str**|  |
 **update_learner_request** | [**UpdateLearnerRequest**](UpdateLearnerRequest.md)|  |

### Return type

[**Learner**](Learner.md)

### Authorization

[bearerAuth](../README.md#bearerAuth)

### HTTP request headers

* **Content-Type**: application/json
* **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | Learner updated successfully |  -  |
**400** | Bad request |  -  |
**401** | Unauthorized |  -  |
**404** | Learner not found |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

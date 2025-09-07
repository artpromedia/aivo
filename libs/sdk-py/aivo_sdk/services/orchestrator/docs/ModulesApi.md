# aivo_sdk.ModulesApi

All URIs are relative to *<https://api.aivo.com/orchestrator/v1>*

Method | HTTP request | Description
------------- | ------------- | -------------
[**add_course_module**](ModulesApi.md#add_course_module) | **POST** /courses/{courseId}/modules | Add module to course
[**get_course_modules**](ModulesApi.md#get_course_modules) | **GET** /courses/{courseId}/modules | Get course modules

# **add_course_module**
>
> Module add_course_module(course_id, create_module_request)

Add module to course

### Example

* Bearer (JWT) Authentication (bearerAuth):

```python
import aivo_sdk
from aivo_sdk.models.create_module_request import CreateModuleRequest
from aivo_sdk.models.module import Module
from aivo_sdk.rest import ApiException
from pprint import pprint

# Defining the host is optional and defaults to https://api.aivo.com/orchestrator/v1
# See configuration.py for a list of all supported configuration parameters.
configuration = aivo_sdk.Configuration(
    host = "https://api.aivo.com/orchestrator/v1"
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
    api_instance = aivo_sdk.ModulesApi(api_client)
    course_id = 'course_id_example' # str | 
    create_module_request = aivo_sdk.CreateModuleRequest() # CreateModuleRequest | 

    try:
        # Add module to course
        api_response = api_instance.add_course_module(course_id, create_module_request)
        print("The response of ModulesApi->add_course_module:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling ModulesApi->add_course_module: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **course_id** | **str**|  |
 **create_module_request** | [**CreateModuleRequest**](CreateModuleRequest.md)|  |

### Return type

[**Module**](Module.md)

### Authorization

[bearerAuth](../README.md#bearerAuth)

### HTTP request headers

* **Content-Type**: application/json
* **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**201** | Module added successfully |  -  |
**400** | Bad request |  -  |
**401** | Unauthorized |  -  |
**404** | Course not found |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **get_course_modules**
>
> List[Module] get_course_modules(course_id)

Get course modules

### Example

* Bearer (JWT) Authentication (bearerAuth):

```python
import aivo_sdk
from aivo_sdk.models.module import Module
from aivo_sdk.rest import ApiException
from pprint import pprint

# Defining the host is optional and defaults to https://api.aivo.com/orchestrator/v1
# See configuration.py for a list of all supported configuration parameters.
configuration = aivo_sdk.Configuration(
    host = "https://api.aivo.com/orchestrator/v1"
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
    api_instance = aivo_sdk.ModulesApi(api_client)
    course_id = 'course_id_example' # str | 

    try:
        # Get course modules
        api_response = api_instance.get_course_modules(course_id)
        print("The response of ModulesApi->get_course_modules:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling ModulesApi->get_course_modules: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **course_id** | **str**|  |

### Return type

[**List[Module]**](Module.md)

### Authorization

[bearerAuth](../README.md#bearerAuth)

### HTTP request headers

* **Content-Type**: Not defined
* **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | Course modules retrieved successfully |  -  |
**401** | Unauthorized |  -  |
**404** | Course not found |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

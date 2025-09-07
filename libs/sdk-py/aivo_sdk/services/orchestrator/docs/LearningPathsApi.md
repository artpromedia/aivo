# aivo_sdk.LearningPathsApi

All URIs are relative to *<https://api.aivo.com/orchestrator/v1>*

Method | HTTP request | Description
------------- | ------------- | -------------
[**create_learning_path**](LearningPathsApi.md#create_learning_path) | **POST** /learning-paths | Create new learning path
[**get_learning_path**](LearningPathsApi.md#get_learning_path) | **GET** /learning-paths/{pathId} | Get learning path by ID
[**list_learning_paths**](LearningPathsApi.md#list_learning_paths) | **GET** /learning-paths | List learning paths

# **create_learning_path**
>
> LearningPath create_learning_path(create_learning_path_request)

Create new learning path

### Example

* Bearer (JWT) Authentication (bearerAuth):

```python
import aivo_sdk
from aivo_sdk.models.create_learning_path_request import CreateLearningPathRequest
from aivo_sdk.models.learning_path import LearningPath
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
    api_instance = aivo_sdk.LearningPathsApi(api_client)
    create_learning_path_request = aivo_sdk.CreateLearningPathRequest() # CreateLearningPathRequest | 

    try:
        # Create new learning path
        api_response = api_instance.create_learning_path(create_learning_path_request)
        print("The response of LearningPathsApi->create_learning_path:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling LearningPathsApi->create_learning_path: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **create_learning_path_request** | [**CreateLearningPathRequest**](CreateLearningPathRequest.md)|  |

### Return type

[**LearningPath**](LearningPath.md)

### Authorization

[bearerAuth](../README.md#bearerAuth)

### HTTP request headers

* **Content-Type**: application/json
* **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**201** | Learning path created successfully |  -  |
**400** | Bad request |  -  |
**401** | Unauthorized |  -  |
**422** | Validation error |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **get_learning_path**
>
> LearningPathDetailed get_learning_path(path_id)

Get learning path by ID

### Example

* Bearer (JWT) Authentication (bearerAuth):

```python
import aivo_sdk
from aivo_sdk.models.learning_path_detailed import LearningPathDetailed
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
    api_instance = aivo_sdk.LearningPathsApi(api_client)
    path_id = 'path_id_example' # str | 

    try:
        # Get learning path by ID
        api_response = api_instance.get_learning_path(path_id)
        print("The response of LearningPathsApi->get_learning_path:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling LearningPathsApi->get_learning_path: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **path_id** | **str**|  |

### Return type

[**LearningPathDetailed**](LearningPathDetailed.md)

### Authorization

[bearerAuth](../README.md#bearerAuth)

### HTTP request headers

* **Content-Type**: Not defined
* **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | Learning path retrieved successfully |  -  |
**401** | Unauthorized |  -  |
**404** | Learning path not found |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **list_learning_paths**
>
> ListLearningPaths200Response list_learning_paths(tenant_id=tenant_id, category=category, status=status, limit=limit, offset=offset)

List learning paths

### Example

* Bearer (JWT) Authentication (bearerAuth):

```python
import aivo_sdk
from aivo_sdk.models.list_learning_paths200_response import ListLearningPaths200Response
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
    api_instance = aivo_sdk.LearningPathsApi(api_client)
    tenant_id = 'tenant_id_example' # str |  (optional)
    category = 'category_example' # str |  (optional)
    status = 'status_example' # str |  (optional)
    limit = 20 # int |  (optional) (default to 20)
    offset = 0 # int |  (optional) (default to 0)

    try:
        # List learning paths
        api_response = api_instance.list_learning_paths(tenant_id=tenant_id, category=category, status=status, limit=limit, offset=offset)
        print("The response of LearningPathsApi->list_learning_paths:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling LearningPathsApi->list_learning_paths: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **tenant_id** | **str**|  | [optional]
 **category** | **str**|  | [optional]
 **status** | **str**|  | [optional]
 **limit** | **int**|  | [optional] [default to 20]
 **offset** | **int**|  | [optional] [default to 0]

### Return type

[**ListLearningPaths200Response**](ListLearningPaths200Response.md)

### Authorization

[bearerAuth](../README.md#bearerAuth)

### HTTP request headers

* **Content-Type**: Not defined
* **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | Learning paths retrieved successfully |  -  |
**401** | Unauthorized |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

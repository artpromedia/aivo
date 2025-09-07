# aivo_sdk.LearnerProfileApi

All URIs are relative to *<https://api.aivo.com/learner/v1>*

Method | HTTP request | Description
------------- | ------------- | -------------
[**get_learner_profile**](LearnerProfileApi.md#get_learner_profile) | **GET** /learners/{learnerId}/profile | Get learner profile
[**update_learner_profile**](LearnerProfileApi.md#update_learner_profile) | **PUT** /learners/{learnerId}/profile | Update learner profile

# **get_learner_profile**
>
> LearnerProfile get_learner_profile(learner_id)

Get learner profile

### Example

* Bearer (JWT) Authentication (bearerAuth):

```python
import aivo_sdk
from aivo_sdk.models.learner_profile import LearnerProfile
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
    api_instance = aivo_sdk.LearnerProfileApi(api_client)
    learner_id = 'learner_id_example' # str | 

    try:
        # Get learner profile
        api_response = api_instance.get_learner_profile(learner_id)
        print("The response of LearnerProfileApi->get_learner_profile:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling LearnerProfileApi->get_learner_profile: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **learner_id** | **str**|  |

### Return type

[**LearnerProfile**](LearnerProfile.md)

### Authorization

[bearerAuth](../README.md#bearerAuth)

### HTTP request headers

* **Content-Type**: Not defined
* **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | Learner profile retrieved successfully |  -  |
**401** | Unauthorized |  -  |
**404** | Learner not found |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **update_learner_profile**
>
> LearnerProfile update_learner_profile(learner_id, update_learner_profile_request)

Update learner profile

### Example

* Bearer (JWT) Authentication (bearerAuth):

```python
import aivo_sdk
from aivo_sdk.models.learner_profile import LearnerProfile
from aivo_sdk.models.update_learner_profile_request import UpdateLearnerProfileRequest
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
    api_instance = aivo_sdk.LearnerProfileApi(api_client)
    learner_id = 'learner_id_example' # str | 
    update_learner_profile_request = aivo_sdk.UpdateLearnerProfileRequest() # UpdateLearnerProfileRequest | 

    try:
        # Update learner profile
        api_response = api_instance.update_learner_profile(learner_id, update_learner_profile_request)
        print("The response of LearnerProfileApi->update_learner_profile:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling LearnerProfileApi->update_learner_profile: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **learner_id** | **str**|  |
 **update_learner_profile_request** | [**UpdateLearnerProfileRequest**](UpdateLearnerProfileRequest.md)|  |

### Return type

[**LearnerProfile**](LearnerProfile.md)

### Authorization

[bearerAuth](../README.md#bearerAuth)

### HTTP request headers

* **Content-Type**: application/json
* **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | Learner profile updated successfully |  -  |
**400** | Bad request |  -  |
**401** | Unauthorized |  -  |
**404** | Learner not found |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# aivo_sdk.AchievementsApi

All URIs are relative to *https://api.aivo.com/learner/v1*

Method | HTTP request | Description
------------- | ------------- | -------------
[**award_achievement**](AchievementsApi.md#award_achievement) | **POST** /learners/{learnerId}/achievements | Award achievement to learner
[**get_learner_achievements**](AchievementsApi.md#get_learner_achievements) | **GET** /learners/{learnerId}/achievements | Get learner achievements


# **award_achievement**
> Achievement award_achievement(learner_id, award_achievement_request)

Award achievement to learner

### Example

* Bearer (JWT) Authentication (bearerAuth):

```python
import aivo_sdk
from aivo_sdk.models.achievement import Achievement
from aivo_sdk.models.award_achievement_request import AwardAchievementRequest
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
    api_instance = aivo_sdk.AchievementsApi(api_client)
    learner_id = 'learner_id_example' # str | 
    award_achievement_request = aivo_sdk.AwardAchievementRequest() # AwardAchievementRequest | 

    try:
        # Award achievement to learner
        api_response = api_instance.award_achievement(learner_id, award_achievement_request)
        print("The response of AchievementsApi->award_achievement:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling AchievementsApi->award_achievement: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **learner_id** | **str**|  | 
 **award_achievement_request** | [**AwardAchievementRequest**](AwardAchievementRequest.md)|  | 

### Return type

[**Achievement**](Achievement.md)

### Authorization

[bearerAuth](../README.md#bearerAuth)

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**201** | Achievement awarded successfully |  -  |
**400** | Bad request |  -  |
**401** | Unauthorized |  -  |
**404** | Learner not found |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **get_learner_achievements**
> List[Achievement] get_learner_achievements(learner_id)

Get learner achievements

### Example

* Bearer (JWT) Authentication (bearerAuth):

```python
import aivo_sdk
from aivo_sdk.models.achievement import Achievement
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
    api_instance = aivo_sdk.AchievementsApi(api_client)
    learner_id = 'learner_id_example' # str | 

    try:
        # Get learner achievements
        api_response = api_instance.get_learner_achievements(learner_id)
        print("The response of AchievementsApi->get_learner_achievements:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling AchievementsApi->get_learner_achievements: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **learner_id** | **str**|  | 

### Return type

[**List[Achievement]**](Achievement.md)

### Authorization

[bearerAuth](../README.md#bearerAuth)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | Learner achievements retrieved successfully |  -  |
**401** | Unauthorized |  -  |
**404** | Learner not found |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)


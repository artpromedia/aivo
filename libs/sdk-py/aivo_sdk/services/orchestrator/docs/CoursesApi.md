# aivo_sdk.CoursesApi

All URIs are relative to *https://api.aivo.com/orchestrator/v1*

Method | HTTP request | Description
------------- | ------------- | -------------
[**create_course**](CoursesApi.md#create_course) | **POST** /courses | Create new course
[**delete_course**](CoursesApi.md#delete_course) | **DELETE** /courses/{courseId} | Delete course
[**get_course**](CoursesApi.md#get_course) | **GET** /courses/{courseId} | Get course by ID
[**list_courses**](CoursesApi.md#list_courses) | **GET** /courses | List courses
[**update_course**](CoursesApi.md#update_course) | **PUT** /courses/{courseId} | Update course


# **create_course**
> Course create_course(create_course_request)

Create new course

### Example

* Bearer (JWT) Authentication (bearerAuth):

```python
import aivo_sdk
from aivo_sdk.models.course import Course
from aivo_sdk.models.create_course_request import CreateCourseRequest
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
    api_instance = aivo_sdk.CoursesApi(api_client)
    create_course_request = aivo_sdk.CreateCourseRequest() # CreateCourseRequest | 

    try:
        # Create new course
        api_response = api_instance.create_course(create_course_request)
        print("The response of CoursesApi->create_course:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling CoursesApi->create_course: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **create_course_request** | [**CreateCourseRequest**](CreateCourseRequest.md)|  | 

### Return type

[**Course**](Course.md)

### Authorization

[bearerAuth](../README.md#bearerAuth)

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**201** | Course created successfully |  -  |
**400** | Bad request |  -  |
**401** | Unauthorized |  -  |
**422** | Validation error |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **delete_course**
> delete_course(course_id)

Delete course

### Example

* Bearer (JWT) Authentication (bearerAuth):

```python
import aivo_sdk
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
    api_instance = aivo_sdk.CoursesApi(api_client)
    course_id = 'course_id_example' # str | 

    try:
        # Delete course
        api_instance.delete_course(course_id)
    except Exception as e:
        print("Exception when calling CoursesApi->delete_course: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **course_id** | **str**|  | 

### Return type

void (empty response body)

### Authorization

[bearerAuth](../README.md#bearerAuth)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**204** | Course deleted successfully |  -  |
**401** | Unauthorized |  -  |
**404** | Course not found |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **get_course**
> CourseDetailed get_course(course_id)

Get course by ID

### Example

* Bearer (JWT) Authentication (bearerAuth):

```python
import aivo_sdk
from aivo_sdk.models.course_detailed import CourseDetailed
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
    api_instance = aivo_sdk.CoursesApi(api_client)
    course_id = 'course_id_example' # str | 

    try:
        # Get course by ID
        api_response = api_instance.get_course(course_id)
        print("The response of CoursesApi->get_course:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling CoursesApi->get_course: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **course_id** | **str**|  | 

### Return type

[**CourseDetailed**](CourseDetailed.md)

### Authorization

[bearerAuth](../README.md#bearerAuth)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | Course retrieved successfully |  -  |
**401** | Unauthorized |  -  |
**404** | Course not found |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **list_courses**
> ListCourses200Response list_courses(tenant_id=tenant_id, category=category, difficulty=difficulty, status=status, search=search, limit=limit, offset=offset)

List courses

### Example

* Bearer (JWT) Authentication (bearerAuth):

```python
import aivo_sdk
from aivo_sdk.models.list_courses200_response import ListCourses200Response
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
    api_instance = aivo_sdk.CoursesApi(api_client)
    tenant_id = 'tenant_id_example' # str |  (optional)
    category = 'category_example' # str |  (optional)
    difficulty = 'difficulty_example' # str |  (optional)
    status = 'status_example' # str |  (optional)
    search = 'search_example' # str |  (optional)
    limit = 20 # int |  (optional) (default to 20)
    offset = 0 # int |  (optional) (default to 0)

    try:
        # List courses
        api_response = api_instance.list_courses(tenant_id=tenant_id, category=category, difficulty=difficulty, status=status, search=search, limit=limit, offset=offset)
        print("The response of CoursesApi->list_courses:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling CoursesApi->list_courses: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **tenant_id** | **str**|  | [optional] 
 **category** | **str**|  | [optional] 
 **difficulty** | **str**|  | [optional] 
 **status** | **str**|  | [optional] 
 **search** | **str**|  | [optional] 
 **limit** | **int**|  | [optional] [default to 20]
 **offset** | **int**|  | [optional] [default to 0]

### Return type

[**ListCourses200Response**](ListCourses200Response.md)

### Authorization

[bearerAuth](../README.md#bearerAuth)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | Courses retrieved successfully |  -  |
**401** | Unauthorized |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **update_course**
> Course update_course(course_id, update_course_request)

Update course

### Example

* Bearer (JWT) Authentication (bearerAuth):

```python
import aivo_sdk
from aivo_sdk.models.course import Course
from aivo_sdk.models.update_course_request import UpdateCourseRequest
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
    api_instance = aivo_sdk.CoursesApi(api_client)
    course_id = 'course_id_example' # str | 
    update_course_request = aivo_sdk.UpdateCourseRequest() # UpdateCourseRequest | 

    try:
        # Update course
        api_response = api_instance.update_course(course_id, update_course_request)
        print("The response of CoursesApi->update_course:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling CoursesApi->update_course: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **course_id** | **str**|  | 
 **update_course_request** | [**UpdateCourseRequest**](UpdateCourseRequest.md)|  | 

### Return type

[**Course**](Course.md)

### Authorization

[bearerAuth](../README.md#bearerAuth)

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | Course updated successfully |  -  |
**400** | Bad request |  -  |
**401** | Unauthorized |  -  |
**404** | Course not found |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)


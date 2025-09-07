# ListCourses200Response

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**data** | [**List[Course]**](Course.md) |  |
**total** | **int** |  |
**limit** | **int** |  |
**offset** | **int** |  |

## Example

```python
from aivo_sdk.models.list_courses200_response import ListCourses200Response

# TODO update the JSON string below
json = "{}"
# create an instance of ListCourses200Response from a JSON string
list_courses200_response_instance = ListCourses200Response.from_json(json)
# print the JSON string representation of the object
print(ListCourses200Response.to_json())

# convert the object into a dict
list_courses200_response_dict = list_courses200_response_instance.to_dict()
# create an instance of ListCourses200Response from a dict
list_courses200_response_from_dict = ListCourses200Response.from_dict(list_courses200_response_dict)
```

[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)

# UpdateCourseRequest

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**title** | **str** |  | [optional]
**description** | **str** |  | [optional]
**short_description** | **str** |  | [optional]
**category** | **str** |  | [optional]
**tags** | **List[str]** |  | [optional]
**difficulty** | **str** |  | [optional]
**status** | **str** |  | [optional]
**estimated_duration** | **int** |  | [optional]
**thumbnail_url** | **str** |  | [optional]
**learning_objectives** | **List[str]** |  | [optional]
**is_public** | **bool** |  | [optional]
**metadata** | **Dict[str, object]** |  | [optional]

## Example

```python
from aivo_sdk.models.update_course_request import UpdateCourseRequest

# TODO update the JSON string below
json = "{}"
# create an instance of UpdateCourseRequest from a JSON string
update_course_request_instance = UpdateCourseRequest.from_json(json)
# print the JSON string representation of the object
print(UpdateCourseRequest.to_json())

# convert the object into a dict
update_course_request_dict = update_course_request_instance.to_dict()
# create an instance of UpdateCourseRequest from a dict
update_course_request_from_dict = UpdateCourseRequest.from_dict(update_course_request_dict)
```

[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)

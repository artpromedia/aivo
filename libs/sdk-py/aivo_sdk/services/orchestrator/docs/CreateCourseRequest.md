# CreateCourseRequest

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**title** | **str** |  |
**description** | **str** |  |
**short_description** | **str** |  | [optional]
**category** | **str** |  |
**tags** | **List[str]** |  | [optional]
**difficulty** | **str** |  |
**estimated_duration** | **int** |  | [optional]
**thumbnail_url** | **str** |  | [optional]
**instructor_id** | **str** |  | [optional]
**prerequisites** | **List[str]** |  | [optional]
**learning_objectives** | **List[str]** |  | [optional]
**is_public** | **bool** |  | [optional] [default to True]
**metadata** | **Dict[str, object]** |  | [optional]

## Example

```python
from aivo_sdk.models.create_course_request import CreateCourseRequest

# TODO update the JSON string below
json = "{}"
# create an instance of CreateCourseRequest from a JSON string
create_course_request_instance = CreateCourseRequest.from_json(json)
# print the JSON string representation of the object
print(CreateCourseRequest.to_json())

# convert the object into a dict
create_course_request_dict = create_course_request_instance.to_dict()
# create an instance of CreateCourseRequest from a dict
create_course_request_from_dict = CreateCourseRequest.from_dict(create_course_request_dict)
```

[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)

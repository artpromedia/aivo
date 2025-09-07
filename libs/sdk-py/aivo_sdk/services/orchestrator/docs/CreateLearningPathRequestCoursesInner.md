# CreateLearningPathRequestCoursesInner

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**course_id** | **str** |  |
**order** | **int** |  |
**is_optional** | **bool** |  | [optional] [default to False]

## Example

```python
from aivo_sdk.models.create_learning_path_request_courses_inner import CreateLearningPathRequestCoursesInner

# TODO update the JSON string below
json = "{}"
# create an instance of CreateLearningPathRequestCoursesInner from a JSON string
create_learning_path_request_courses_inner_instance = CreateLearningPathRequestCoursesInner.from_json(json)
# print the JSON string representation of the object
print(CreateLearningPathRequestCoursesInner.to_json())

# convert the object into a dict
create_learning_path_request_courses_inner_dict = create_learning_path_request_courses_inner_instance.to_dict()
# create an instance of CreateLearningPathRequestCoursesInner from a dict
create_learning_path_request_courses_inner_from_dict = CreateLearningPathRequestCoursesInner.from_dict(create_learning_path_request_courses_inner_dict)
```

[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)

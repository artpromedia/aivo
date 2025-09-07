# Course

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**id** | **str** |  |
**title** | **str** |  |
**description** | **str** |  |
**short_description** | **str** |  | [optional]
**category** | **str** |  |
**tags** | **List[str]** |  | [optional]
**difficulty** | **str** |  |
**status** | **str** |  |
**estimated_duration** | **int** | Estimated duration in minutes |
**thumbnail_url** | **str** |  | [optional]
**instructor_id** | **str** |  | [optional]
**prerequisites** | **List[str]** |  | [optional]
**learning_objectives** | **List[str]** |  | [optional]
**module_count** | **int** |  | [optional]
**enrollment_count** | **int** |  | [optional]
**average_rating** | **float** |  | [optional]
**review_count** | **int** |  | [optional]
**is_public** | **bool** |  | [optional] [default to True]
**metadata** | **Dict[str, object]** |  | [optional]
**created_at** | **datetime** |  |
**updated_at** | **datetime** |  |

## Example

```python
from aivo_sdk.models.course import Course

# TODO update the JSON string below
json = "{}"
# create an instance of Course from a JSON string
course_instance = Course.from_json(json)
# print the JSON string representation of the object
print(Course.to_json())

# convert the object into a dict
course_dict = course_instance.to_dict()
# create an instance of Course from a dict
course_from_dict = Course.from_dict(course_dict)
```

[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)

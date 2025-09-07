# Assessment

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**id** | **str** |  |
**title** | **str** |  |
**description** | **str** |  | [optional]
**type** | **str** |  |
**course_id** | **str** |  |
**module_id** | **str** |  | [optional]
**max_score** | **float** |  |
**passing_score** | **float** |  |
**time_limit** | **int** | Time limit in minutes |
**attempts_allowed** | **int** |  | [optional]
**question_count** | **int** |  | [optional]
**is_required** | **bool** |  | [optional] [default to True]
**metadata** | **Dict[str, object]** |  | [optional]
**created_at** | **datetime** |  |
**updated_at** | **datetime** |  |

## Example

```python
from aivo_sdk.models.assessment import Assessment

# TODO update the JSON string below
json = "{}"
# create an instance of Assessment from a JSON string
assessment_instance = Assessment.from_json(json)
# print the JSON string representation of the object
print(Assessment.to_json())

# convert the object into a dict
assessment_dict = assessment_instance.to_dict()
# create an instance of Assessment from a dict
assessment_from_dict = Assessment.from_dict(assessment_dict)
```

[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)

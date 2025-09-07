# LearningPath

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**id** | **str** |  |
**title** | **str** |  |
**description** | **str** |  |
**category** | **str** |  |
**status** | **str** |  |
**difficulty** | **str** |  | [optional]
**estimated_duration** | **int** | Total estimated duration in minutes |
**thumbnail_url** | **str** |  | [optional]
**course_count** | **int** |  |
**enrollment_count** | **int** |  | [optional]
**average_rating** | **float** |  | [optional]
**tags** | **List[str]** |  | [optional]
**created_at** | **datetime** |  |
**updated_at** | **datetime** |  |

## Example

```python
from aivo_sdk.models.learning_path import LearningPath

# TODO update the JSON string below
json = "{}"
# create an instance of LearningPath from a JSON string
learning_path_instance = LearningPath.from_json(json)
# print the JSON string representation of the object
print(LearningPath.to_json())

# convert the object into a dict
learning_path_dict = learning_path_instance.to_dict()
# create an instance of LearningPath from a dict
learning_path_from_dict = LearningPath.from_dict(learning_path_dict)
```

[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)

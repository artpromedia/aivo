# CreateLearningPathRequest

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**title** | **str** |  |
**description** | **str** |  |
**category** | **str** |  |
**difficulty** | **str** |  | [optional]
**thumbnail_url** | **str** |  | [optional]
**tags** | **List[str]** |  | [optional]
**courses** | [**List[CreateLearningPathRequestCoursesInner]**](CreateLearningPathRequestCoursesInner.md) |  |

## Example

```python
from aivo_sdk.models.create_learning_path_request import CreateLearningPathRequest

# TODO update the JSON string below
json = "{}"
# create an instance of CreateLearningPathRequest from a JSON string
create_learning_path_request_instance = CreateLearningPathRequest.from_json(json)
# print the JSON string representation of the object
print(CreateLearningPathRequest.to_json())

# convert the object into a dict
create_learning_path_request_dict = create_learning_path_request_instance.to_dict()
# create an instance of CreateLearningPathRequest from a dict
create_learning_path_request_from_dict = CreateLearningPathRequest.from_dict(create_learning_path_request_dict)
```

[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)

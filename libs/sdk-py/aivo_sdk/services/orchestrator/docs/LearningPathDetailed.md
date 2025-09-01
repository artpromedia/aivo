# LearningPathDetailed


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
**courses** | [**List[LearningPathDetailedAllOfCourses]**](LearningPathDetailedAllOfCourses.md) |  | [optional] 

## Example

```python
from aivo_sdk.models.learning_path_detailed import LearningPathDetailed

# TODO update the JSON string below
json = "{}"
# create an instance of LearningPathDetailed from a JSON string
learning_path_detailed_instance = LearningPathDetailed.from_json(json)
# print the JSON string representation of the object
print(LearningPathDetailed.to_json())

# convert the object into a dict
learning_path_detailed_dict = learning_path_detailed_instance.to_dict()
# create an instance of LearningPathDetailed from a dict
learning_path_detailed_from_dict = LearningPathDetailed.from_dict(learning_path_detailed_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)



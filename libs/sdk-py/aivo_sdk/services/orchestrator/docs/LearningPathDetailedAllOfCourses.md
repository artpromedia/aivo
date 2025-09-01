# LearningPathDetailedAllOfCourses


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**course_id** | **str** |  | [optional] 
**course** | [**Course**](Course.md) |  | [optional] 
**order** | **int** |  | [optional] 
**is_optional** | **bool** |  | [optional] 
**unlock_conditions** | [**LearningPathDetailedAllOfUnlockConditions**](LearningPathDetailedAllOfUnlockConditions.md) |  | [optional] 

## Example

```python
from aivo_sdk.models.learning_path_detailed_all_of_courses import LearningPathDetailedAllOfCourses

# TODO update the JSON string below
json = "{}"
# create an instance of LearningPathDetailedAllOfCourses from a JSON string
learning_path_detailed_all_of_courses_instance = LearningPathDetailedAllOfCourses.from_json(json)
# print the JSON string representation of the object
print(LearningPathDetailedAllOfCourses.to_json())

# convert the object into a dict
learning_path_detailed_all_of_courses_dict = learning_path_detailed_all_of_courses_instance.to_dict()
# create an instance of LearningPathDetailedAllOfCourses from a dict
learning_path_detailed_all_of_courses_from_dict = LearningPathDetailedAllOfCourses.from_dict(learning_path_detailed_all_of_courses_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)



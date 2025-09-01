# LearnerProfileGoalsInner


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**goal_id** | **str** |  | [optional] 
**title** | **str** |  | [optional] 
**description** | **str** |  | [optional] 
**target_date** | **date** |  | [optional] 
**status** | **str** |  | [optional] 
**progress** | **float** |  | [optional] 

## Example

```python
from aivo_sdk.models.learner_profile_goals_inner import LearnerProfileGoalsInner

# TODO update the JSON string below
json = "{}"
# create an instance of LearnerProfileGoalsInner from a JSON string
learner_profile_goals_inner_instance = LearnerProfileGoalsInner.from_json(json)
# print the JSON string representation of the object
print(LearnerProfileGoalsInner.to_json())

# convert the object into a dict
learner_profile_goals_inner_dict = learner_profile_goals_inner_instance.to_dict()
# create an instance of LearnerProfileGoalsInner from a dict
learner_profile_goals_inner_from_dict = LearnerProfileGoalsInner.from_dict(learner_profile_goals_inner_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)



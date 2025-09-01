# LearnerProfilePreferences


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**learning_style** | **str** |  | [optional] 
**difficulty_level** | **str** |  | [optional] 
**notifications_enabled** | **bool** |  | [optional] [default to True]
**email_digest** | **bool** |  | [optional] [default to True]
**preferred_learning_time** | **str** |  | [optional] 

## Example

```python
from aivo_sdk.models.learner_profile_preferences import LearnerProfilePreferences

# TODO update the JSON string below
json = "{}"
# create an instance of LearnerProfilePreferences from a JSON string
learner_profile_preferences_instance = LearnerProfilePreferences.from_json(json)
# print the JSON string representation of the object
print(LearnerProfilePreferences.to_json())

# convert the object into a dict
learner_profile_preferences_dict = learner_profile_preferences_instance.to_dict()
# create an instance of LearnerProfilePreferences from a dict
learner_profile_preferences_from_dict = LearnerProfilePreferences.from_dict(learner_profile_preferences_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)



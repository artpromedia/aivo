# LearnerProfileSkillsInner

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**skill_id** | **str** |  | [optional]
**skill_name** | **str** |  | [optional]
**level** | **str** |  | [optional]
**verified_at** | **datetime** |  | [optional]

## Example

```python
from aivo_sdk.models.learner_profile_skills_inner import LearnerProfileSkillsInner

# TODO update the JSON string below
json = "{}"
# create an instance of LearnerProfileSkillsInner from a JSON string
learner_profile_skills_inner_instance = LearnerProfileSkillsInner.from_json(json)
# print the JSON string representation of the object
print(LearnerProfileSkillsInner.to_json())

# convert the object into a dict
learner_profile_skills_inner_dict = learner_profile_skills_inner_instance.to_dict()
# create an instance of LearnerProfileSkillsInner from a dict
learner_profile_skills_inner_from_dict = LearnerProfileSkillsInner.from_dict(learner_profile_skills_inner_dict)
```

[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)

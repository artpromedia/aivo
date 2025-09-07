# Learner

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**id** | **str** |  |
**tenant_id** | **str** |  |
**email** | **str** |  |
**first_name** | **str** |  |
**last_name** | **str** |  |
**status** | **str** |  |
**avatar** | **str** |  | [optional]
**timezone** | **str** |  | [optional]
**language** | **str** |  | [optional]
**department** | **str** |  | [optional]
**job_title** | **str** |  | [optional]
**manager** | **str** |  | [optional]
**last_login_at** | **datetime** |  | [optional]
**enrollment_count** | **int** |  | [optional]
**completion_count** | **int** |  | [optional]
**total_learning_minutes** | **int** |  | [optional]
**metadata** | **Dict[str, object]** |  | [optional]
**created_at** | **datetime** |  |
**updated_at** | **datetime** |  |

## Example

```python
from aivo_sdk.models.learner import Learner

# TODO update the JSON string below
json = "{}"
# create an instance of Learner from a JSON string
learner_instance = Learner.from_json(json)
# print the JSON string representation of the object
print(Learner.to_json())

# convert the object into a dict
learner_dict = learner_instance.to_dict()
# create an instance of Learner from a dict
learner_from_dict = Learner.from_dict(learner_dict)
```

[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)

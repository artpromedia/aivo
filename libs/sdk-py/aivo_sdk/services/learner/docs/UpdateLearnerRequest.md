# UpdateLearnerRequest

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**first_name** | **str** |  | [optional]
**last_name** | **str** |  | [optional]
**status** | **str** |  | [optional]
**timezone** | **str** |  | [optional]
**language** | **str** |  | [optional]
**department** | **str** |  | [optional]
**job_title** | **str** |  | [optional]
**manager** | **str** |  | [optional]
**metadata** | **Dict[str, object]** |  | [optional]

## Example

```python
from aivo_sdk.models.update_learner_request import UpdateLearnerRequest

# TODO update the JSON string below
json = "{}"
# create an instance of UpdateLearnerRequest from a JSON string
update_learner_request_instance = UpdateLearnerRequest.from_json(json)
# print the JSON string representation of the object
print(UpdateLearnerRequest.to_json())

# convert the object into a dict
update_learner_request_dict = update_learner_request_instance.to_dict()
# create an instance of UpdateLearnerRequest from a dict
update_learner_request_from_dict = UpdateLearnerRequest.from_dict(update_learner_request_dict)
```

[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)

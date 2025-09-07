# UpdateSubscriptionRequest

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**plan_id** | **str** |  | [optional]
**quantity** | **int** |  | [optional]
**metadata** | **Dict[str, object]** |  | [optional]

## Example

```python
from aivo_sdk.models.update_subscription_request import UpdateSubscriptionRequest

# TODO update the JSON string below
json = "{}"
# create an instance of UpdateSubscriptionRequest from a JSON string
update_subscription_request_instance = UpdateSubscriptionRequest.from_json(json)
# print the JSON string representation of the object
print(UpdateSubscriptionRequest.to_json())

# convert the object into a dict
update_subscription_request_dict = update_subscription_request_instance.to_dict()
# create an instance of UpdateSubscriptionRequest from a dict
update_subscription_request_from_dict = UpdateSubscriptionRequest.from_dict(update_subscription_request_dict)
```

[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)

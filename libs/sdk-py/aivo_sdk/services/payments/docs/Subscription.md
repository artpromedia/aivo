# Subscription


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**id** | **str** |  | 
**tenant_id** | **str** |  | 
**plan_id** | **str** |  | 
**status** | **str** |  | 
**quantity** | **int** |  | [optional] 
**unit_amount** | **int** | Amount in cents | [optional] 
**currency** | **str** |  | [optional] 
**current_period_start** | **datetime** |  | 
**current_period_end** | **datetime** |  | 
**trial_start** | **datetime** |  | [optional] 
**trial_end** | **datetime** |  | [optional] 
**cancel_at_period_end** | **bool** |  | [optional] [default to False]
**canceled_at** | **datetime** |  | [optional] 
**discount** | [**Discount**](Discount.md) |  | [optional] 
**metadata** | **Dict[str, object]** |  | [optional] 
**created_at** | **datetime** |  | 
**updated_at** | **datetime** |  | 

## Example

```python
from aivo_sdk.models.subscription import Subscription

# TODO update the JSON string below
json = "{}"
# create an instance of Subscription from a JSON string
subscription_instance = Subscription.from_json(json)
# print the JSON string representation of the object
print(Subscription.to_json())

# convert the object into a dict
subscription_dict = subscription_instance.to_dict()
# create an instance of Subscription from a dict
subscription_from_dict = Subscription.from_dict(subscription_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)



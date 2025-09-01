# SubscriptionDetailsPlan


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**name** | **str** | Plan name | 
**tier** | **str** |  | 
**features** | **List[str]** |  | 
**price_per_seat** | **float** | Price per seat per month | [optional] 

## Example

```python
from aivo_sdk.models.subscription_details_plan import SubscriptionDetailsPlan

# TODO update the JSON string below
json = "{}"
# create an instance of SubscriptionDetailsPlan from a JSON string
subscription_details_plan_instance = SubscriptionDetailsPlan.from_json(json)
# print the JSON string representation of the object
print(SubscriptionDetailsPlan.to_json())

# convert the object into a dict
subscription_details_plan_dict = subscription_details_plan_instance.to_dict()
# create an instance of SubscriptionDetailsPlan from a dict
subscription_details_plan_from_dict = SubscriptionDetailsPlan.from_dict(subscription_details_plan_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)



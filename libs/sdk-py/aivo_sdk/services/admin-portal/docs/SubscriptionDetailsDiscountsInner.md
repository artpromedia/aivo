# SubscriptionDetailsDiscountsInner

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**name** | **str** |  | [optional]
**type** | **str** |  | [optional]
**value** | **float** |  | [optional]
**description** | **str** |  | [optional]

## Example

```python
from aivo_sdk.models.subscription_details_discounts_inner import SubscriptionDetailsDiscountsInner

# TODO update the JSON string below
json = "{}"
# create an instance of SubscriptionDetailsDiscountsInner from a JSON string
subscription_details_discounts_inner_instance = SubscriptionDetailsDiscountsInner.from_json(json)
# print the JSON string representation of the object
print(SubscriptionDetailsDiscountsInner.to_json())

# convert the object into a dict
subscription_details_discounts_inner_dict = subscription_details_discounts_inner_instance.to_dict()
# create an instance of SubscriptionDetailsDiscountsInner from a dict
subscription_details_discounts_inner_from_dict = SubscriptionDetailsDiscountsInner.from_dict(subscription_details_discounts_inner_dict)
```

[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)

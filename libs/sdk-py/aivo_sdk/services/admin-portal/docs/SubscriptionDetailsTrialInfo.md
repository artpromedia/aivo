# SubscriptionDetailsTrialInfo


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**is_trialing** | **bool** |  | [optional] 
**trial_ends_at** | **datetime** |  | [optional] 
**days_remaining** | **int** |  | [optional] 

## Example

```python
from aivo_sdk.models.subscription_details_trial_info import SubscriptionDetailsTrialInfo

# TODO update the JSON string below
json = "{}"
# create an instance of SubscriptionDetailsTrialInfo from a JSON string
subscription_details_trial_info_instance = SubscriptionDetailsTrialInfo.from_json(json)
# print the JSON string representation of the object
print(SubscriptionDetailsTrialInfo.to_json())

# convert the object into a dict
subscription_details_trial_info_dict = subscription_details_trial_info_instance.to_dict()
# create an instance of SubscriptionDetailsTrialInfo from a dict
subscription_details_trial_info_from_dict = SubscriptionDetailsTrialInfo.from_dict(subscription_details_trial_info_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)



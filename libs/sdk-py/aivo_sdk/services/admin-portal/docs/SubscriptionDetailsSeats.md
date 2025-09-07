# SubscriptionDetailsSeats

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**current** | **int** | Current number of seats |
**included** | **int** | Seats included in base plan |
**additional** | **int** | Additional seats purchased |

## Example

```python
from aivo_sdk.models.subscription_details_seats import SubscriptionDetailsSeats

# TODO update the JSON string below
json = "{}"
# create an instance of SubscriptionDetailsSeats from a JSON string
subscription_details_seats_instance = SubscriptionDetailsSeats.from_json(json)
# print the JSON string representation of the object
print(SubscriptionDetailsSeats.to_json())

# convert the object into a dict
subscription_details_seats_dict = subscription_details_seats_instance.to_dict()
# create an instance of SubscriptionDetailsSeats from a dict
subscription_details_seats_from_dict = SubscriptionDetailsSeats.from_dict(subscription_details_seats_dict)
```

[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)

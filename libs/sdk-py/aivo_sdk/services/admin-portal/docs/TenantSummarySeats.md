# TenantSummarySeats

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**total** | **int** | Total seats in subscription |
**free** | **int** | Number of free/available seats |
**reserved** | **int** | Number of reserved seats |
**assigned** | **int** | Number of assigned seats |

## Example

```python
from aivo_sdk.models.tenant_summary_seats import TenantSummarySeats

# TODO update the JSON string below
json = "{}"
# create an instance of TenantSummarySeats from a JSON string
tenant_summary_seats_instance = TenantSummarySeats.from_json(json)
# print the JSON string representation of the object
print(TenantSummarySeats.to_json())

# convert the object into a dict
tenant_summary_seats_dict = tenant_summary_seats_instance.to_dict()
# create an instance of TenantSummarySeats from a dict
tenant_summary_seats_from_dict = TenantSummarySeats.from_dict(tenant_summary_seats_dict)
```

[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)

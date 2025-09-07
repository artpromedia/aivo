# TenantSummary

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**tenant_id** | **str** |  |
**learners** | [**TenantSummaryLearners**](TenantSummaryLearners.md) |  |
**seats** | [**TenantSummarySeats**](TenantSummarySeats.md) |  |
**trial_count** | **int** | Number of learners currently in trial |
**open_approvals** | **int** | Number of pending approval requests |
**enrollment_stats** | [**TenantSummaryEnrollmentStats**](TenantSummaryEnrollmentStats.md) |  | [optional]
**last_updated** | **datetime** | When this summary was last calculated |

## Example

```python
from aivo_sdk.models.tenant_summary import TenantSummary

# TODO update the JSON string below
json = "{}"
# create an instance of TenantSummary from a JSON string
tenant_summary_instance = TenantSummary.from_json(json)
# print the JSON string representation of the object
print(TenantSummary.to_json())

# convert the object into a dict
tenant_summary_dict = tenant_summary_instance.to_dict()
# create an instance of TenantSummary from a dict
tenant_summary_from_dict = TenantSummary.from_dict(tenant_summary_dict)
```

[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)

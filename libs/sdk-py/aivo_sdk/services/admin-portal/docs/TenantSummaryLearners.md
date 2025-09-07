# TenantSummaryLearners

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**total** | **int** | Total number of learners |
**active** | **int** | Number of active learners |
**inactive** | **int** | Number of inactive learners |
**pending** | **int** | Number of pending learners |

## Example

```python
from aivo_sdk.models.tenant_summary_learners import TenantSummaryLearners

# TODO update the JSON string below
json = "{}"
# create an instance of TenantSummaryLearners from a JSON string
tenant_summary_learners_instance = TenantSummaryLearners.from_json(json)
# print the JSON string representation of the object
print(TenantSummaryLearners.to_json())

# convert the object into a dict
tenant_summary_learners_dict = tenant_summary_learners_instance.to_dict()
# create an instance of TenantSummaryLearners from a dict
tenant_summary_learners_from_dict = TenantSummaryLearners.from_dict(tenant_summary_learners_dict)
```

[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)

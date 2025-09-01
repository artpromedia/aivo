# TenantSummaryEnrollmentStats


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**total_enrollments** | **int** |  | [optional] 
**active_enrollments** | **int** |  | [optional] 
**completed_this_month** | **int** |  | [optional] 

## Example

```python
from aivo_sdk.models.tenant_summary_enrollment_stats import TenantSummaryEnrollmentStats

# TODO update the JSON string below
json = "{}"
# create an instance of TenantSummaryEnrollmentStats from a JSON string
tenant_summary_enrollment_stats_instance = TenantSummaryEnrollmentStats.from_json(json)
# print the JSON string representation of the object
print(TenantSummaryEnrollmentStats.to_json())

# convert the object into a dict
tenant_summary_enrollment_stats_dict = tenant_summary_enrollment_stats_instance.to_dict()
# create an instance of TenantSummaryEnrollmentStats from a dict
tenant_summary_enrollment_stats_from_dict = TenantSummaryEnrollmentStats.from_dict(tenant_summary_enrollment_stats_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)



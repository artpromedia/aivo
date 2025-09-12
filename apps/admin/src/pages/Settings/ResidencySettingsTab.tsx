import { Save, AlertCircle, CheckCircle, Shield, MapPin } from 'lucide-react';
import { useState, useEffect } from 'react';

import { Alert, AlertDescription } from '@/components/ui/alert';
import { Button } from '@/components/ui/button';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { Checkbox } from '@/components/ui/checkbox';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select } from '@/components/ui/select';
import {
  useResidencySettings,
  useUpdateResidencySettings,
  type ResidencySettings,
} from '@/hooks/useSettings';

// Region options
const REGIONS = [
  {
    value: 'us-east',
    label: 'US East (N. Virginia)',
    description: 'Primary US data center',
  },
  {
    value: 'us-west',
    label: 'US West (Oregon)',
    description: 'Secondary US data center',
  },
  {
    value: 'eu-west',
    label: 'EU West (Ireland)',
    description: 'European Union compliant',
  },
  {
    value: 'eu-central',
    label: 'EU Central (Frankfurt)',
    description: 'German data protection laws',
  },
  {
    value: 'ap-southeast',
    label: 'AP Southeast (Sydney)',
    description: 'Asia-Pacific region',
  },
  {
    value: 'ap-northeast',
    label: 'AP Northeast (Tokyo)',
    description: 'Japan data center',
  },
  {
    value: 'ca-central',
    label: 'Canada Central (Toronto)',
    description: 'Canadian data sovereignty',
  },
];

// Processing purposes
const PROCESSING_PURPOSES = [
  {
    value: 'educational',
    label: 'Educational Analytics',
    description: 'Learning progress and performance',
  },
  {
    value: 'operational',
    label: 'Operational Analytics',
    description: 'System performance and usage',
  },
  {
    value: 'research',
    label: 'Educational Research',
    description: 'Anonymized research studies',
  },
  {
    value: 'safety',
    label: 'Safety & Security',
    description: 'Content moderation and security',
  },
  {
    value: 'support',
    label: 'Customer Support',
    description: 'Technical support and troubleshooting',
  },
];

// Compliance frameworks
const COMPLIANCE_FRAMEWORKS = [
  {
    value: 'FERPA',
    label: 'FERPA (US)',
    description: 'Family Educational Rights and Privacy Act',
  },
  {
    value: 'COPPA',
    label: 'COPPA (US)',
    description: "Children's Online Privacy Protection Act",
  },
  {
    value: 'GDPR',
    label: 'GDPR (EU)',
    description: 'General Data Protection Regulation',
  },
  {
    value: 'CCPA',
    label: 'CCPA (California)',
    description: 'California Consumer Privacy Act',
  },
  {
    value: 'PIPEDA',
    label: 'PIPEDA (Canada)',
    description: 'Personal Information Protection Act',
  },
  { value: 'SOX', label: 'SOX (US)', description: 'Sarbanes-Oxley Act' },
];

export function ResidencySettingsTab() {
  const {
    data: residencySettingsData,
    isLoading,
    error,
  } = useResidencySettings();
  const updateResidencySettings = useUpdateResidencySettings();

  const [formData, setFormData] = useState<ResidencySettings>({
    region: 'us-east',
    processing_purposes: ['educational'],
    data_retention_days: 2555, // 7 years
    cross_border_transfer: false,
    compliance_framework: 'FERPA',
  });

  const [hasChanges, setHasChanges] = useState(false);

  // Update form when data loads
  useEffect(() => {
    if (residencySettingsData?.settings) {
      setFormData(residencySettingsData.settings as ResidencySettings);
    }
  }, [residencySettingsData]);

  const handleInputChange = (
    field: keyof ResidencySettings,
    value: string | number | boolean | string[]
  ) => {
    setFormData(prev => ({
      ...prev,
      [field]: value,
    }));
    setHasChanges(true);
  };

  const handleProcessingPurposeChange = (purpose: string, checked: boolean) => {
    const currentPurposes = formData.processing_purposes || [];
    const newPurposes = checked
      ? [...currentPurposes, purpose]
      : currentPurposes.filter(p => p !== purpose);

    handleInputChange('processing_purposes', newPurposes);
  };

  const handleSave = async () => {
    try {
      await updateResidencySettings.mutateAsync(formData);
      setHasChanges(false);
    } catch {
      // Error is handled by the mutation
    }
  };

  const getRegionInfo = (regionValue: string) => {
    return REGIONS.find(r => r.value === regionValue);
  };

  if (isLoading) {
    return (
      <div className='flex items-center justify-center h-64'>
        <div className='text-lg'>Loading data residency settings...</div>
      </div>
    );
  }

  if (error) {
    return (
      <Alert variant='destructive'>
        <AlertCircle className='h-4 w-4' />
        <AlertDescription>
          Failed to load data residency settings. Please try again.
        </AlertDescription>
      </Alert>
    );
  }

  return (
    <div className='space-y-6'>
      {updateResidencySettings.isSuccess && (
        <Alert>
          <CheckCircle className='h-4 w-4' />
          <AlertDescription>
            Data residency settings updated successfully!
          </AlertDescription>
        </Alert>
      )}

      {updateResidencySettings.isError && (
        <Alert variant='destructive'>
          <AlertCircle className='h-4 w-4' />
          <AlertDescription>
            Failed to update data residency settings. Please try again.
          </AlertDescription>
        </Alert>
      )}

      <div className='grid gap-6'>
        {/* Data Region */}
        <Card>
          <CardHeader>
            <CardTitle className='flex items-center space-x-2'>
              <MapPin className='h-5 w-5' />
              <span>Data Region</span>
            </CardTitle>
            <CardDescription>
              Choose where your organization's data will be stored and processed
            </CardDescription>
          </CardHeader>
          <CardContent className='space-y-4'>
            <div className='grid gap-2'>
              <Label htmlFor='region'>Primary Data Region</Label>
              <Select
                value={formData.region || 'us-east'}
                onChange={e => handleInputChange('region', e.target.value)}
              >
                {REGIONS.map(region => (
                  <option key={region.value} value={region.value}>
                    {region.label}
                  </option>
                ))}
              </Select>
              {formData.region && (
                <p className='text-sm text-muted-foreground'>
                  {getRegionInfo(formData.region)?.description}
                </p>
              )}
            </div>

            <div className='flex items-center space-x-2'>
              <Checkbox
                id='cross_border_transfer'
                checked={formData.cross_border_transfer || false}
                onCheckedChange={(checked: boolean) =>
                  handleInputChange('cross_border_transfer', checked)
                }
              />
              <Label htmlFor='cross_border_transfer' className='text-sm'>
                Allow cross-border data transfers for operational purposes
              </Label>
            </div>
          </CardContent>
        </Card>

        {/* Processing Purposes */}
        <Card>
          <CardHeader>
            <CardTitle>Data Processing Purposes</CardTitle>
            <CardDescription>
              Select the permitted purposes for data processing
            </CardDescription>
          </CardHeader>
          <CardContent className='space-y-4'>
            {PROCESSING_PURPOSES.map(purpose => (
              <div key={purpose.value} className='flex items-start space-x-3'>
                <Checkbox
                  id={`purpose_${purpose.value}`}
                  checked={
                    formData.processing_purposes?.includes(purpose.value) ||
                    false
                  }
                  onCheckedChange={(checked: boolean) =>
                    handleProcessingPurposeChange(purpose.value, checked)
                  }
                />
                <div className='space-y-1'>
                  <Label
                    htmlFor={`purpose_${purpose.value}`}
                    className='text-sm font-medium'
                  >
                    {purpose.label}
                  </Label>
                  <p className='text-sm text-muted-foreground'>
                    {purpose.description}
                  </p>
                </div>
              </div>
            ))}
          </CardContent>
        </Card>

        {/* Compliance & Retention */}
        <Card>
          <CardHeader>
            <CardTitle className='flex items-center space-x-2'>
              <Shield className='h-5 w-5' />
              <span>Compliance & Retention</span>
            </CardTitle>
            <CardDescription>
              Configure compliance framework and data retention policies
            </CardDescription>
          </CardHeader>
          <CardContent className='space-y-4'>
            <div className='grid gap-2'>
              <Label htmlFor='compliance_framework'>Compliance Framework</Label>
              <Select
                value={formData.compliance_framework || 'FERPA'}
                onChange={e =>
                  handleInputChange('compliance_framework', e.target.value)
                }
              >
                {COMPLIANCE_FRAMEWORKS.map(framework => (
                  <option key={framework.value} value={framework.value}>
                    {framework.label}
                  </option>
                ))}
              </Select>
              {formData.compliance_framework && (
                <p className='text-sm text-muted-foreground'>
                  {
                    COMPLIANCE_FRAMEWORKS.find(
                      f => f.value === formData.compliance_framework
                    )?.description
                  }
                </p>
              )}
            </div>

            <div className='grid gap-2'>
              <Label htmlFor='data_retention_days'>
                Data Retention Period (Days)
              </Label>
              <Input
                id='data_retention_days'
                type='number'
                min='30'
                max='3650'
                value={formData.data_retention_days || 2555}
                onChange={e =>
                  handleInputChange(
                    'data_retention_days',
                    parseInt(e.target.value)
                  )
                }
              />
              <p className='text-sm text-muted-foreground'>
                Current setting:{' '}
                {Math.round(
                  ((formData.data_retention_days || 2555) / 365) * 10
                ) / 10}{' '}
                years
                {formData.compliance_framework === 'FERPA' &&
                  ' (FERPA recommends 7+ years)'}
                {formData.compliance_framework === 'GDPR' &&
                  ' (GDPR allows up to 6 years for legitimate interests)'}
              </p>
            </div>
          </CardContent>
        </Card>

        {/* Impact Notice */}
        <Alert>
          <Shield className='h-4 w-4' />
          <AlertDescription>
            <strong>Important:</strong> Changes to data residency settings may
            affect model dispatch routing and require data migration. Some
            regions may have different AI model availability. Contact support
            before changing regions in production environments.
          </AlertDescription>
        </Alert>

        {/* Save Button */}
        <div className='flex justify-end'>
          <Button
            onClick={handleSave}
            disabled={!hasChanges || updateResidencySettings.isPending}
            className='min-w-32'
          >
            {updateResidencySettings.isPending ? (
              <div className='flex items-center space-x-2'>
                <div className='w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin' />
                <span>Saving...</span>
              </div>
            ) : (
              <div className='flex items-center space-x-2'>
                <Save className='h-4 w-4' />
                <span>Save Changes</span>
              </div>
            )}
          </Button>
        </div>
      </div>
    </div>
  );
}

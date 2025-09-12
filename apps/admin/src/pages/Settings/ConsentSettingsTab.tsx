import {
  Save,
  AlertCircle,
  CheckCircle,
  UserCheck,
  Shield,
} from 'lucide-react';
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
  useConsentSettings,
  useUpdateConsentSettings,
  type ConsentSettings,
} from '@/hooks/useSettings';

// Withdrawal process options
const WITHDRAWAL_PROCESSES = [
  {
    value: 'contact_support',
    label: 'Contact Support',
    description: 'Users must contact support to withdraw consent',
  },
  {
    value: 'self_service',
    label: 'Self-Service Portal',
    description: 'Users can withdraw consent through account settings',
  },
  {
    value: 'email_request',
    label: 'Email Request',
    description: 'Users can email a request to withdraw consent',
  },
  {
    value: 'automated',
    label: 'Automated System',
    description: 'Automated consent withdrawal via API',
  },
];

export function ConsentSettingsTab() {
  const { data: consentSettingsData, isLoading, error } = useConsentSettings();
  const updateConsentSettings = useUpdateConsentSettings();

  const [formData, setFormData] = useState<ConsentSettings>({
    media_default: false,
    analytics_opt_in: true,
    retention_days: 2555, // 7 years
    parental_consent_required: true,
    consent_expiry_days: 365,
    withdrawal_process: 'contact_support',
  });

  const [hasChanges, setHasChanges] = useState(false);

  // Update form when data loads
  useEffect(() => {
    if (consentSettingsData?.settings) {
      setFormData(consentSettingsData.settings as ConsentSettings);
    }
  }, [consentSettingsData]);

  const handleInputChange = (
    field: keyof ConsentSettings,
    value: string | number | boolean
  ) => {
    setFormData(prev => ({
      ...prev,
      [field]: value,
    }));
    setHasChanges(true);
  };

  const handleSave = async () => {
    try {
      await updateConsentSettings.mutateAsync(formData);
      setHasChanges(false);
    } catch {
      // Error is handled by the mutation
    }
  };

  if (isLoading) {
    return (
      <div className='flex items-center justify-center h-64'>
        <div className='text-lg'>Loading consent settings...</div>
      </div>
    );
  }

  if (error) {
    return (
      <Alert variant='destructive'>
        <AlertCircle className='h-4 w-4' />
        <AlertDescription>
          Failed to load consent settings. Please try again.
        </AlertDescription>
      </Alert>
    );
  }

  return (
    <div className='space-y-6'>
      {updateConsentSettings.isSuccess && (
        <Alert>
          <CheckCircle className='h-4 w-4' />
          <AlertDescription>
            Consent settings updated successfully!
          </AlertDescription>
        </Alert>
      )}

      {updateConsentSettings.isError && (
        <Alert variant='destructive'>
          <AlertCircle className='h-4 w-4' />
          <AlertDescription>
            Failed to update consent settings. Please try again.
          </AlertDescription>
        </Alert>
      )}

      <div className='grid gap-6'>
        {/* Default Consent Settings */}
        <Card>
          <CardHeader>
            <CardTitle className='flex items-center space-x-2'>
              <UserCheck className='h-5 w-5' />
              <span>Default Consent Settings</span>
            </CardTitle>
            <CardDescription>
              Configure default consent preferences for new users and learners
            </CardDescription>
          </CardHeader>
          <CardContent className='space-y-4'>
            <div className='flex items-center space-x-2'>
              <Checkbox
                id='media_default'
                checked={formData.media_default || false}
                onCheckedChange={(checked: boolean) =>
                  handleInputChange('media_default', checked)
                }
              />
              <div className='space-y-1'>
                <Label htmlFor='media_default' className='text-sm font-medium'>
                  Default media capture consent
                </Label>
                <p className='text-sm text-muted-foreground'>
                  New users will have media capture (camera, microphone) enabled
                  by default
                </p>
              </div>
            </div>

            <div className='flex items-center space-x-2'>
              <Checkbox
                id='analytics_opt_in'
                checked={formData.analytics_opt_in || false}
                onCheckedChange={(checked: boolean) =>
                  handleInputChange('analytics_opt_in', checked)
                }
              />
              <div className='space-y-1'>
                <Label
                  htmlFor='analytics_opt_in'
                  className='text-sm font-medium'
                >
                  Default analytics opt-in
                </Label>
                <p className='text-sm text-muted-foreground'>
                  New users will be opted into learning analytics by default
                </p>
              </div>
            </div>

            <div className='flex items-center space-x-2'>
              <Checkbox
                id='parental_consent_required'
                checked={formData.parental_consent_required || false}
                onCheckedChange={(checked: boolean) =>
                  handleInputChange('parental_consent_required', checked)
                }
              />
              <div className='space-y-1'>
                <Label
                  htmlFor='parental_consent_required'
                  className='text-sm font-medium'
                >
                  Require parental consent for minors
                </Label>
                <p className='text-sm text-muted-foreground'>
                  Users under 13 (or local age of consent) require parental
                  approval
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Consent Management */}
        <Card>
          <CardHeader>
            <CardTitle>Consent Management</CardTitle>
            <CardDescription>
              Configure how consent is managed and maintained over time
            </CardDescription>
          </CardHeader>
          <CardContent className='space-y-4'>
            <div className='grid gap-2'>
              <Label htmlFor='consent_expiry_days'>
                Consent Expiry Period (Days)
              </Label>
              <Input
                id='consent_expiry_days'
                type='number'
                min='30'
                max='1095'
                value={formData.consent_expiry_days || 365}
                onChange={e =>
                  handleInputChange(
                    'consent_expiry_days',
                    parseInt(e.target.value)
                  )
                }
              />
              <p className='text-sm text-muted-foreground'>
                Consent will expire after this period and require renewal.
                Current setting:{' '}
                {Math.round(((formData.consent_expiry_days || 365) / 30) * 10) /
                  10}{' '}
                months
              </p>
            </div>

            <div className='grid gap-2'>
              <Label htmlFor='withdrawal_process'>
                Consent Withdrawal Process
              </Label>
              <Select
                value={formData.withdrawal_process || 'contact_support'}
                onChange={e =>
                  handleInputChange('withdrawal_process', e.target.value)
                }
              >
                {WITHDRAWAL_PROCESSES.map(process => (
                  <option key={process.value} value={process.value}>
                    {process.label}
                  </option>
                ))}
              </Select>
              {formData.withdrawal_process && (
                <p className='text-sm text-muted-foreground'>
                  {
                    WITHDRAWAL_PROCESSES.find(
                      p => p.value === formData.withdrawal_process
                    )?.description
                  }
                </p>
              )}
            </div>
          </CardContent>
        </Card>

        {/* Data Retention for Consent */}
        <Card>
          <CardHeader>
            <CardTitle className='flex items-center space-x-2'>
              <Shield className='h-5 w-5' />
              <span>Data Retention</span>
            </CardTitle>
            <CardDescription>
              Configure how long data is retained based on consent status
            </CardDescription>
          </CardHeader>
          <CardContent className='space-y-4'>
            <div className='grid gap-2'>
              <Label htmlFor='retention_days'>
                Data Retention Period (Days)
              </Label>
              <Input
                id='retention_days'
                type='number'
                min='30'
                max='3650'
                value={formData.retention_days || 2555}
                onChange={e =>
                  handleInputChange('retention_days', parseInt(e.target.value))
                }
              />
              <p className='text-sm text-muted-foreground'>
                How long to retain data after consent is withdrawn. Current
                setting:{' '}
                {Math.round(((formData.retention_days || 2555) / 365) * 10) /
                  10}{' '}
                years
              </p>
            </div>
          </CardContent>
        </Card>

        {/* Privacy Impact Notice */}
        <Alert>
          <UserCheck className='h-4 w-4' />
          <AlertDescription>
            <strong>Privacy Compliance:</strong> These settings affect privacy
            compliance for COPPA, GDPR, and other regulations. Ensure your
            consent mechanisms meet local legal requirements. Consider
            consulting with legal counsel for regulatory compliance.
          </AlertDescription>
        </Alert>

        {/* Compliance Summary */}
        <Card>
          <CardHeader>
            <CardTitle>Compliance Summary</CardTitle>
            <CardDescription>
              How your current settings align with privacy regulations
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className='space-y-3'>
              <div className='flex items-center justify-between p-3 bg-green-50 rounded-lg'>
                <div>
                  <div className='font-medium text-green-800'>
                    COPPA Compliance
                  </div>
                  <div className='text-sm text-green-600'>
                    {formData.parental_consent_required
                      ? 'Enabled'
                      : 'Disabled'}{' '}
                    - Parental consent for under 13
                  </div>
                </div>
                <div
                  className={`px-2 py-1 rounded text-xs font-medium ${
                    formData.parental_consent_required
                      ? 'bg-green-100 text-green-800'
                      : 'bg-yellow-100 text-yellow-800'
                  }`}
                >
                  {formData.parental_consent_required
                    ? 'Compliant'
                    : 'Check Required'}
                </div>
              </div>

              <div className='flex items-center justify-between p-3 bg-blue-50 rounded-lg'>
                <div>
                  <div className='font-medium text-blue-800'>
                    GDPR Compliance
                  </div>
                  <div className='text-sm text-blue-600'>
                    Data retention:{' '}
                    {Math.round(
                      ((formData.retention_days || 2555) / 365) * 10
                    ) / 10}{' '}
                    years
                  </div>
                </div>
                <div
                  className={`px-2 py-1 rounded text-xs font-medium ${
                    (formData.retention_days || 2555) <= 2190
                      ? 'bg-green-100 text-green-800'
                      : 'bg-yellow-100 text-yellow-800'
                  }`}
                >
                  {(formData.retention_days || 2555) <= 2190
                    ? 'Within Guidelines'
                    : 'Review Needed'}
                </div>
              </div>

              <div className='flex items-center justify-between p-3 bg-purple-50 rounded-lg'>
                <div>
                  <div className='font-medium text-purple-800'>
                    FERPA Compliance
                  </div>
                  <div className='text-sm text-purple-600'>
                    Educational data retention and consent management
                  </div>
                </div>
                <div className='px-2 py-1 rounded text-xs font-medium bg-green-100 text-green-800'>
                  Compliant
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Save Button */}
        <div className='flex justify-end'>
          <Button
            onClick={handleSave}
            disabled={!hasChanges || updateConsentSettings.isPending}
            className='min-w-32'
          >
            {updateConsentSettings.isPending ? (
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

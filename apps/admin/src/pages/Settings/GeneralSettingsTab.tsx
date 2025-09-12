import { Save, AlertCircle, CheckCircle } from 'lucide-react';
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
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
  useOrgSettings,
  useUpdateOrgSettings,
  type OrgSettings,
} from '@/hooks/useSettings';

export function GeneralSettingsTab() {
  const { data: orgSettingsData, isLoading, error } = useOrgSettings();
  const updateOrgSettings = useUpdateOrgSettings();

  const [formData, setFormData] = useState<OrgSettings>({
    brand_name: '',
    logo_url: '',
    primary_color: '#3B82F6',
    support_email: '',
    website_url: '',
    privacy_policy_url: '',
    terms_of_service_url: '',
  });

  const [hasChanges, setHasChanges] = useState(false);

  // Update form when data loads
  useEffect(() => {
    if (orgSettingsData?.settings) {
      setFormData(orgSettingsData.settings as OrgSettings);
    }
  }, [orgSettingsData]);

  const handleInputChange = (field: keyof OrgSettings, value: string) => {
    setFormData(prev => ({
      ...prev,
      [field]: value,
    }));
    setHasChanges(true);
  };

  const handleSave = async () => {
    try {
      await updateOrgSettings.mutateAsync(formData);
      setHasChanges(false);
    } catch {
      // Error is handled by the mutation
    }
  };

  const handleLogoUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      // In a real implementation, you'd upload to a file storage service
      // For now, we'll just create a URL for the file
      const url = URL.createObjectURL(file);
      handleInputChange('logo_url', url);
    }
  };

  if (isLoading) {
    return (
      <div className='flex items-center justify-center h-64'>
        <div className='text-lg'>Loading organization settings...</div>
      </div>
    );
  }

  if (error) {
    return (
      <Alert>
        <AlertCircle className='h-4 w-4' />
        <AlertDescription>
          Failed to load organization settings. Please try again.
        </AlertDescription>
      </Alert>
    );
  }

  return (
    <div className='space-y-6'>
      {updateOrgSettings.isSuccess && (
        <Alert>
          <CheckCircle className='h-4 w-4' />
          <AlertDescription>
            Organization settings updated successfully!
          </AlertDescription>
        </Alert>
      )}

      {updateOrgSettings.isError && (
        <Alert variant='destructive'>
          <AlertCircle className='h-4 w-4' />
          <AlertDescription>
            Failed to update organization settings. Please try again.
          </AlertDescription>
        </Alert>
      )}

      <div className='grid gap-6'>
        {/* Branding Section */}
        <Card>
          <CardHeader>
            <CardTitle>Branding</CardTitle>
            <CardDescription>
              Configure your organization's brand identity
            </CardDescription>
          </CardHeader>
          <CardContent className='space-y-4'>
            <div className='grid gap-2'>
              <Label htmlFor='brand_name'>Organization Name</Label>
              <Input
                id='brand_name'
                value={formData.brand_name || ''}
                onChange={e => handleInputChange('brand_name', e.target.value)}
                placeholder='AIVO Education'
              />
            </div>

            <div className='grid gap-2'>
              <Label htmlFor='logo_upload'>Logo</Label>
              <div className='flex items-center space-x-4'>
                {formData.logo_url && (
                  <img
                    src={formData.logo_url}
                    alt='Organization logo'
                    className='h-12 w-12 object-contain border rounded'
                  />
                )}
                <div className='flex-1'>
                  <Input
                    id='logo_upload'
                    type='file'
                    accept='image/*'
                    onChange={handleLogoUpload}
                    className='cursor-pointer'
                  />
                  <p className='text-sm text-muted-foreground mt-1'>
                    Upload a logo image (PNG, JPG, SVG)
                  </p>
                </div>
              </div>
            </div>

            <div className='grid gap-2'>
              <Label htmlFor='primary_color'>Primary Color</Label>
              <div className='flex items-center space-x-2'>
                <Input
                  id='primary_color'
                  type='color'
                  value={formData.primary_color || '#3B82F6'}
                  onChange={e =>
                    handleInputChange('primary_color', e.target.value)
                  }
                  className='w-20 h-10 cursor-pointer'
                />
                <Input
                  value={formData.primary_color || '#3B82F6'}
                  onChange={e =>
                    handleInputChange('primary_color', e.target.value)
                  }
                  placeholder='#3B82F6'
                  className='flex-1'
                />
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Contact Information */}
        <Card>
          <CardHeader>
            <CardTitle>Contact Information</CardTitle>
            <CardDescription>
              Configure contact details for your organization
            </CardDescription>
          </CardHeader>
          <CardContent className='space-y-4'>
            <div className='grid gap-2'>
              <Label htmlFor='support_email'>Support Email</Label>
              <Input
                id='support_email'
                type='email'
                value={formData.support_email || ''}
                onChange={e =>
                  handleInputChange('support_email', e.target.value)
                }
                placeholder='support@aivo.education'
              />
            </div>

            <div className='grid gap-2'>
              <Label htmlFor='website_url'>Website URL</Label>
              <Input
                id='website_url'
                type='url'
                value={formData.website_url || ''}
                onChange={e => handleInputChange('website_url', e.target.value)}
                placeholder='https://aivo.education'
              />
            </div>
          </CardContent>
        </Card>

        {/* Legal URLs */}
        <Card>
          <CardHeader>
            <CardTitle>Legal Information</CardTitle>
            <CardDescription>
              Configure links to your legal documents
            </CardDescription>
          </CardHeader>
          <CardContent className='space-y-4'>
            <div className='grid gap-2'>
              <Label htmlFor='privacy_policy_url'>Privacy Policy URL</Label>
              <Input
                id='privacy_policy_url'
                type='url'
                value={formData.privacy_policy_url || ''}
                onChange={e =>
                  handleInputChange('privacy_policy_url', e.target.value)
                }
                placeholder='https://aivo.education/privacy'
              />
            </div>

            <div className='grid gap-2'>
              <Label htmlFor='terms_of_service_url'>Terms of Service URL</Label>
              <Input
                id='terms_of_service_url'
                type='url'
                value={formData.terms_of_service_url || ''}
                onChange={e =>
                  handleInputChange('terms_of_service_url', e.target.value)
                }
                placeholder='https://aivo.education/terms'
              />
            </div>
          </CardContent>
        </Card>

        {/* Save Button */}
        <div className='flex justify-end'>
          <Button
            onClick={handleSave}
            disabled={!hasChanges || updateOrgSettings.isPending}
            className='min-w-32'
          >
            {updateOrgSettings.isPending ? (
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

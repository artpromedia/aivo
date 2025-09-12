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
import { Label } from '@/components/ui/label';
import { Select } from '@/components/ui/select';
import {
  useLocaleSettings,
  useUpdateLocaleSettings,
  type LocaleSettings,
} from '@/hooks/useSettings';

// Locale options
const LOCALES = [
  { value: 'en-US', label: 'English (US)' },
  { value: 'en-GB', label: 'English (UK)' },
  { value: 'es-ES', label: 'Spanish (Spain)' },
  { value: 'es-MX', label: 'Spanish (Mexico)' },
  { value: 'fr-FR', label: 'French (France)' },
  { value: 'de-DE', label: 'German (Germany)' },
  { value: 'pt-BR', label: 'Portuguese (Brazil)' },
  { value: 'zh-CN', label: 'Chinese (Simplified)' },
  { value: 'ja-JP', label: 'Japanese' },
];

const TIMEZONES = [
  { value: 'UTC', label: 'UTC' },
  { value: 'America/New_York', label: 'Eastern Time (US)' },
  { value: 'America/Chicago', label: 'Central Time (US)' },
  { value: 'America/Denver', label: 'Mountain Time (US)' },
  { value: 'America/Los_Angeles', label: 'Pacific Time (US)' },
  { value: 'Europe/London', label: 'GMT (London)' },
  { value: 'Europe/Paris', label: 'CET (Paris)' },
  { value: 'Asia/Tokyo', label: 'JST (Tokyo)' },
  { value: 'Australia/Sydney', label: 'AEST (Sydney)' },
];

const DATE_FORMATS = [
  { value: 'MM/DD/YYYY', label: 'MM/DD/YYYY (US)' },
  { value: 'DD/MM/YYYY', label: 'DD/MM/YYYY (UK)' },
  { value: 'YYYY-MM-DD', label: 'YYYY-MM-DD (ISO)' },
  { value: 'DD.MM.YYYY', label: 'DD.MM.YYYY (German)' },
];

const CURRENCIES = [
  { value: 'USD', label: 'US Dollar ($)' },
  { value: 'EUR', label: 'Euro (€)' },
  { value: 'GBP', label: 'British Pound (£)' },
  { value: 'CAD', label: 'Canadian Dollar (C$)' },
  { value: 'AUD', label: 'Australian Dollar (A$)' },
  { value: 'JPY', label: 'Japanese Yen (¥)' },
  { value: 'BRL', label: 'Brazilian Real (R$)' },
];

const GRADE_SCHEMES = [
  { value: 'letter', label: 'Letter Grades (A-F)' },
  { value: 'percentage', label: 'Percentage (0-100%)' },
  { value: 'points_4', label: 'Points (0-4.0)' },
  { value: 'points_10', label: 'Points (1-10)' },
  { value: 'points_100', label: 'Points (0-100)' },
];

const DAYS_OF_WEEK = [
  { value: 0, label: 'Sunday' },
  { value: 1, label: 'Monday' },
  { value: 2, label: 'Tuesday' },
  { value: 3, label: 'Wednesday' },
  { value: 4, label: 'Thursday' },
  { value: 5, label: 'Friday' },
  { value: 6, label: 'Saturday' },
];

export function LocalizationSettingsTab() {
  const { data: localeSettingsData, isLoading, error } = useLocaleSettings();
  const updateLocaleSettings = useUpdateLocaleSettings();

  const [formData, setFormData] = useState<LocaleSettings>({
    default_locale: 'en-US',
    time_zone: 'UTC',
    date_format: 'MM/DD/YYYY',
    currency: 'USD',
    grade_scheme: 'letter',
    first_day_of_week: 0,
  });

  const [hasChanges, setHasChanges] = useState(false);

  // Update form when data loads
  useEffect(() => {
    if (localeSettingsData?.settings) {
      setFormData(localeSettingsData.settings as LocaleSettings);
    }
  }, [localeSettingsData]);

  const handleInputChange = (
    field: keyof LocaleSettings,
    value: string | number
  ) => {
    setFormData(prev => ({
      ...prev,
      [field]: value,
    }));
    setHasChanges(true);
  };

  const handleSave = async () => {
    try {
      await updateLocaleSettings.mutateAsync(formData);
      setHasChanges(false);
    } catch {
      // Error is handled by the mutation
    }
  };

  if (isLoading) {
    return (
      <div className='flex items-center justify-center h-64'>
        <div className='text-lg'>Loading localization settings...</div>
      </div>
    );
  }

  if (error) {
    return (
      <Alert variant='destructive'>
        <AlertCircle className='h-4 w-4' />
        <AlertDescription>
          Failed to load localization settings. Please try again.
        </AlertDescription>
      </Alert>
    );
  }

  return (
    <div className='space-y-6'>
      {updateLocaleSettings.isSuccess && (
        <Alert>
          <CheckCircle className='h-4 w-4' />
          <AlertDescription>
            Localization settings updated successfully!
          </AlertDescription>
        </Alert>
      )}

      {updateLocaleSettings.isError && (
        <Alert variant='destructive'>
          <AlertCircle className='h-4 w-4' />
          <AlertDescription>
            Failed to update localization settings. Please try again.
          </AlertDescription>
        </Alert>
      )}

      <div className='grid gap-6'>
        {/* Language & Locale */}
        <Card>
          <CardHeader>
            <CardTitle>Language & Locale</CardTitle>
            <CardDescription>
              Configure default language and regional settings
            </CardDescription>
          </CardHeader>
          <CardContent className='space-y-4'>
            <div className='grid gap-2'>
              <Label htmlFor='default_locale'>Default Language</Label>
              <Select
                value={formData.default_locale || 'en-US'}
                onChange={e =>
                  handleInputChange('default_locale', e.target.value)
                }
              >
                {LOCALES.map(locale => (
                  <option key={locale.value} value={locale.value}>
                    {locale.label}
                  </option>
                ))}
              </Select>
            </div>

            <div className='grid gap-2'>
              <Label htmlFor='time_zone'>Time Zone</Label>
              <Select
                value={formData.time_zone || 'UTC'}
                onChange={e => handleInputChange('time_zone', e.target.value)}
              >
                {TIMEZONES.map(tz => (
                  <option key={tz.value} value={tz.value}>
                    {tz.label}
                  </option>
                ))}
              </Select>
            </div>
          </CardContent>
        </Card>

        {/* Formatting */}
        <Card>
          <CardHeader>
            <CardTitle>Formatting</CardTitle>
            <CardDescription>
              Configure date, currency, and grade formatting
            </CardDescription>
          </CardHeader>
          <CardContent className='space-y-4'>
            <div className='grid gap-2'>
              <Label htmlFor='date_format'>Date Format</Label>
              <Select
                value={formData.date_format || 'MM/DD/YYYY'}
                onChange={e => handleInputChange('date_format', e.target.value)}
              >
                {DATE_FORMATS.map(format => (
                  <option key={format.value} value={format.value}>
                    {format.label}
                  </option>
                ))}
              </Select>
            </div>

            <div className='grid gap-2'>
              <Label htmlFor='currency'>Currency</Label>
              <Select
                value={formData.currency || 'USD'}
                onChange={e => handleInputChange('currency', e.target.value)}
              >
                {CURRENCIES.map(currency => (
                  <option key={currency.value} value={currency.value}>
                    {currency.label}
                  </option>
                ))}
              </Select>
            </div>

            <div className='grid gap-2'>
              <Label htmlFor='grade_scheme'>Grade Scheme</Label>
              <Select
                value={formData.grade_scheme || 'letter'}
                onChange={e =>
                  handleInputChange('grade_scheme', e.target.value)
                }
              >
                {GRADE_SCHEMES.map(scheme => (
                  <option key={scheme.value} value={scheme.value}>
                    {scheme.label}
                  </option>
                ))}
              </Select>
            </div>

            <div className='grid gap-2'>
              <Label htmlFor='first_day_of_week'>First Day of Week</Label>
              <Select
                value={String(formData.first_day_of_week || 0)}
                onChange={e =>
                  handleInputChange(
                    'first_day_of_week',
                    parseInt(e.target.value)
                  )
                }
              >
                {DAYS_OF_WEEK.map(day => (
                  <option key={day.value} value={day.value}>
                    {day.label}
                  </option>
                ))}
              </Select>
            </div>
          </CardContent>
        </Card>

        {/* Preview */}
        <Card>
          <CardHeader>
            <CardTitle>Preview</CardTitle>
            <CardDescription>
              See how your formatting choices will appear
            </CardDescription>
          </CardHeader>
          <CardContent className='space-y-2'>
            <div className='text-sm'>
              <strong>Date:</strong>{' '}
              {new Date().toLocaleDateString(formData.default_locale, {
                timeZone: formData.time_zone,
              })}
            </div>
            <div className='text-sm'>
              <strong>Currency:</strong>{' '}
              {new Intl.NumberFormat(formData.default_locale, {
                style: 'currency',
                currency: formData.currency,
              }).format(1234.56)}
            </div>
            <div className='text-sm'>
              <strong>Grade Example:</strong>{' '}
              {formData.grade_scheme === 'letter'
                ? 'A-'
                : formData.grade_scheme === 'percentage'
                  ? '87%'
                  : formData.grade_scheme === 'points_4'
                    ? '3.7/4.0'
                    : formData.grade_scheme === 'points_10'
                      ? '8.7/10'
                      : '87/100'}
            </div>
          </CardContent>
        </Card>

        {/* Save Button */}
        <div className='flex justify-end'>
          <Button
            onClick={handleSave}
            disabled={!hasChanges || updateLocaleSettings.isPending}
            className='min-w-32'
          >
            {updateLocaleSettings.isPending ? (
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

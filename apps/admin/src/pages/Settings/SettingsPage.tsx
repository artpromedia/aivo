import { Settings2, Building2, Globe, Shield, UserCheck } from 'lucide-react';
import { useState } from 'react';

import { ConsentSettingsTab } from './ConsentSettingsTab';
import { GeneralSettingsTab } from './GeneralSettingsTab';
import { LocalizationSettingsTab } from './LocalizationSettingsTab';
import { ResidencySettingsTab } from './ResidencySettingsTab';

import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';

export function SettingsPage() {
  const [activeTab, setActiveTab] = useState('general');

  return (
    <div className='space-y-6'>
      {/* Header */}
      <div className='flex items-center justify-between'>
        <div>
          <h1 className='text-3xl font-bold tracking-tight'>
            Organization Settings
          </h1>
          <p className='text-muted-foreground'>
            Configure organization-wide settings for branding, localization,
            data residency, and consent defaults
          </p>
        </div>
        <div className='flex items-center space-x-2'>
          <Settings2 className='h-6 w-6 text-muted-foreground' />
        </div>
      </div>

      {/* Settings Tabs */}
      <Tabs
        value={activeTab}
        onValueChange={setActiveTab}
        className='space-y-6'
      >
        <TabsList className='grid w-full grid-cols-4'>
          <TabsTrigger value='general' className='flex items-center space-x-2'>
            <Building2 className='h-4 w-4' />
            <span>General</span>
          </TabsTrigger>
          <TabsTrigger
            value='localization'
            className='flex items-center space-x-2'
          >
            <Globe className='h-4 w-4' />
            <span>Localization</span>
          </TabsTrigger>
          <TabsTrigger
            value='residency'
            className='flex items-center space-x-2'
          >
            <Shield className='h-4 w-4' />
            <span>Residency</span>
          </TabsTrigger>
          <TabsTrigger value='consent' className='flex items-center space-x-2'>
            <UserCheck className='h-4 w-4' />
            <span>Consent</span>
          </TabsTrigger>
        </TabsList>

        <TabsContent value='general' className='space-y-6'>
          <Card>
            <CardHeader>
              <CardTitle className='flex items-center space-x-2'>
                <Building2 className='h-5 w-5' />
                <span>General Settings</span>
              </CardTitle>
              <CardDescription>
                Configure organization branding, contact information, and
                general preferences
              </CardDescription>
            </CardHeader>
            <CardContent>
              <GeneralSettingsTab />
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value='localization' className='space-y-6'>
          <Card>
            <CardHeader>
              <CardTitle className='flex items-center space-x-2'>
                <Globe className='h-5 w-5' />
                <span>Localization Settings</span>
              </CardTitle>
              <CardDescription>
                Configure default locale, timezone, currency, and formatting
                preferences
              </CardDescription>
            </CardHeader>
            <CardContent>
              <LocalizationSettingsTab />
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value='residency' className='space-y-6'>
          <Card>
            <CardHeader>
              <CardTitle className='flex items-center space-x-2'>
                <Shield className='h-5 w-5' />
                <span>Data Residency Settings</span>
              </CardTitle>
              <CardDescription>
                Configure data processing regions, compliance frameworks, and
                retention policies
              </CardDescription>
            </CardHeader>
            <CardContent>
              <ResidencySettingsTab />
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value='consent' className='space-y-6'>
          <Card>
            <CardHeader>
              <CardTitle className='flex items-center space-x-2'>
                <UserCheck className='h-5 w-5' />
                <span>Consent Defaults</span>
              </CardTitle>
              <CardDescription>
                Configure default consent settings for media capture, analytics,
                and data retention
              </CardDescription>
            </CardHeader>
            <CardContent>
              <ConsentSettingsTab />
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}

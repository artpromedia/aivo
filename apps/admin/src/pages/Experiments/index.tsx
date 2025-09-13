import { useState } from 'react';

import { Experiments } from './Experiments';
import { Flags } from './Flags';

import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';


export function ExperimentsPage() {
  const [activeTab, setActiveTab] = useState('flags');

  return (
    <div className='space-y-6'>
      <div>
        <h1 className='text-3xl font-bold tracking-tight'>
          Experiments & Feature Flags
        </h1>
        <p className='text-muted-foreground'>
          Manage feature flags and run experiments to optimize your application.
        </p>
      </div>

      <Tabs
        value={activeTab}
        onValueChange={setActiveTab}
        className='space-y-4'
      >
        <TabsList className='grid w-full grid-cols-2'>
          <TabsTrigger value='flags'>Feature Flags</TabsTrigger>
          <TabsTrigger value='experiments'>Experiments</TabsTrigger>
        </TabsList>

        <TabsContent value='flags' className='space-y-4'>
          <Card>
            <CardHeader>
              <CardTitle>Feature Flags</CardTitle>
              <CardDescription>
                Control feature rollouts with tenant-scoped flags and
                percentage-based targeting.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <Flags />
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value='experiments' className='space-y-4'>
          <Card>
            <CardHeader>
              <CardTitle>Experiments</CardTitle>
              <CardDescription>
                Run A/B tests and analyze experiment results to make data-driven
                decisions.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <Experiments />
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}

import { useQuery } from '@tanstack/react-query';
import {
  Beaker,
  BarChart3,
  Users,
  Play,
  Award,
  AlertCircle,
  CheckCircle,
} from 'lucide-react';
import React, { useState } from 'react';

import {
  FlagsAPI,
  type Experiment,
  type ExperimentAnalytics,
  type FeatureFlag,
} from '@/api/flags';
import { Badge } from '@/components/ui/badge';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';

// Metric card component
const MetricCard = ({
  title,
  value,
  icon: Icon,
  trend,
  trendValue,
}: {
  title: string;
  value: string | number;
  icon: React.ComponentType<{ className?: string }>;
  trend?: 'up' | 'down' | 'neutral';
  trendValue?: string;
}) => (
  <Card>
    <CardContent className='p-4'>
      <div className='flex items-center justify-between'>
        <div>
          <p className='text-sm font-medium text-gray-600'>{title}</p>
          <p className='text-2xl font-bold'>{value}</p>
          {trend && trendValue && (
            <p
              className={`text-xs ${trend === 'up' ? 'text-green-600' : trend === 'down' ? 'text-red-600' : 'text-gray-600'}`}
            >
              {trendValue}
            </p>
          )}
        </div>
        <Icon className='h-8 w-8 text-gray-400' />
      </div>
    </CardContent>
  </Card>
);

// Experiment overview component
const ExperimentOverview = ({
  experiment,
  analytics,
}: {
  experiment: Experiment;
  analytics?: ExperimentAnalytics;
}) => (
  <Card>
    <CardHeader>
      <div className='flex items-center justify-between'>
        <div className='flex items-center space-x-2'>
          <Beaker className='h-5 w-5 text-blue-500' />
          <CardTitle>{experiment.name}</CardTitle>
        </div>
        <Badge
          variant={
            experiment.status === 'running'
              ? 'default'
              : experiment.status === 'completed'
                ? 'secondary'
                : 'outline'
          }
        >
          {experiment.status}
        </Badge>
      </div>
    </CardHeader>
    <CardContent>
      <div className='space-y-4'>
        <div>
          <p className='text-sm text-gray-600'>{experiment.description}</p>
          {experiment.hypothesis && (
            <div className='mt-2'>
              <p className='text-xs font-medium text-gray-500'>Hypothesis:</p>
              <p className='text-sm text-gray-700'>{experiment.hypothesis}</p>
            </div>
          )}
        </div>

        {/* Experiment dates */}
        <div className='grid grid-cols-2 gap-4 text-sm'>
          <div>
            <p className='font-medium text-gray-500'>Start Date</p>
            <p>
              {experiment.start_date
                ? new Date(experiment.start_date).toLocaleDateString()
                : 'Not started'}
            </p>
          </div>
          <div>
            <p className='font-medium text-gray-500'>End Date</p>
            <p>
              {experiment.end_date
                ? new Date(experiment.end_date).toLocaleDateString()
                : 'Ongoing'}
            </p>
          </div>
        </div>

        {/* Variants */}
        <div>
          <p className='font-medium text-gray-500 mb-2'>Variants</p>
          <div className='space-y-2'>
            {experiment.variants.map((variant, index) => (
              <div
                key={index}
                className='flex items-center justify-between p-2 bg-gray-50 rounded'
              >
                <span className='font-medium'>{variant.name}</span>
                <span className='text-sm text-gray-600'>{variant.weight}%</span>
              </div>
            ))}
          </div>
        </div>

        {/* Success metrics */}
        {experiment.success_metrics.length > 0 && (
          <div>
            <p className='font-medium text-gray-500 mb-2'>Success Metrics</p>
            <div className='flex flex-wrap gap-1'>
              {experiment.success_metrics.map((metric, index) => (
                <Badge key={index} variant='default'>
                  {metric}
                </Badge>
              ))}
            </div>
          </div>
        )}

        {/* Statistical significance */}
        {analytics?.statistical_significance && (
          <div className='flex items-center space-x-2'>
            {analytics.statistical_significance > 0.95 ? (
              <CheckCircle className='h-4 w-4 text-green-500' />
            ) : (
              <AlertCircle className='h-4 w-4 text-yellow-500' />
            )}
            <span className='text-sm'>
              Statistical Significance:{' '}
              {(analytics.statistical_significance * 100).toFixed(1)}%
            </span>
          </div>
        )}
      </div>
    </CardContent>
  </Card>
);

// Main Experiments component
export function Experiments() {
  const [selectedTab, setSelectedTab] = useState('overview');
  const [selectedExperiment, setSelectedExperiment] = useState<string | null>(
    null
  );

  // Fetch all feature flags that are experiments
  const { data: flags = [], isLoading: flagsLoading } = useQuery({
    queryKey: ['feature-flags-experiments'],
    queryFn: () => FlagsAPI.listFlags({ is_experiment: true }),
  });

  // Fetch experiments for selected flag
  const { data: experiments = [] } = useQuery({
    queryKey: ['experiments', selectedExperiment],
    queryFn: () =>
      selectedExperiment
        ? FlagsAPI.listExperiments(selectedExperiment)
        : Promise.resolve([]),
    enabled: !!selectedExperiment,
  });

  // Fetch analytics for running experiments
  const { data: analyticsData } = useQuery({
    queryKey: ['experiment-analytics', experiments.map(e => e.experiment_id)],
    queryFn: async () => {
      const analytics = await Promise.allSettled(
        experiments
          .filter(exp => exp.status === 'running')
          .map(exp => FlagsAPI.getExperimentAnalytics(exp.experiment_id))
      );

      const results: Record<string, ExperimentAnalytics> = {};
      analytics.forEach((result, index) => {
        if (result.status === 'fulfilled') {
          const experiment = experiments.filter(
            exp => exp.status === 'running'
          )[index];
          if (experiment) {
            results[experiment.experiment_id] = result.value;
          }
        }
      });

      return results;
    },
    enabled: experiments.some(exp => exp.status === 'running'),
  });

  const runningExperiments = experiments.filter(
    exp => exp.status === 'running'
  );
  const completedExperiments = experiments.filter(
    exp => exp.status === 'completed'
  );

  if (flagsLoading) {
    return (
      <div className='p-6'>
        <div className='animate-pulse space-y-4'>
          <div className='h-8 bg-gray-200 rounded w-1/4'></div>
          <div className='h-32 bg-gray-200 rounded'></div>
        </div>
      </div>
    );
  }

  return (
    <div className='p-6'>
      <div className='flex items-center justify-between mb-6'>
        <div>
          <h1 className='text-2xl font-bold flex items-center gap-2'>
            <Beaker className='w-6 h-6' />
            Experiments
          </h1>
          <p className='text-gray-600'>
            Monitor experiment performance and analyze results
          </p>
        </div>
      </div>

      {/* Experiment selector */}
      <Card className='mb-6'>
        <CardContent className='pt-4'>
          <div className='flex items-center gap-4'>
            <label className='text-sm font-medium'>
              Select Experiment Flag:
            </label>
            <select
              value={selectedExperiment || ''}
              onChange={e => setSelectedExperiment(e.target.value || null)}
              className='border rounded px-3 py-2'
            >
              <option value=''>Choose an experiment...</option>
              {flags.map((flag: FeatureFlag) => (
                <option key={flag.key} value={flag.key}>
                  {flag.name} ({flag.key})
                </option>
              ))}
            </select>
          </div>
        </CardContent>
      </Card>

      {selectedExperiment && experiments.length > 0 && (
        <Tabs value={selectedTab} onValueChange={setSelectedTab}>
          <TabsList>
            <TabsTrigger value='overview'>Overview</TabsTrigger>
            <TabsTrigger value='analytics'>Analytics</TabsTrigger>
            <TabsTrigger value='results'>Results</TabsTrigger>
          </TabsList>

          <TabsContent value='overview'>
            <div className='space-y-6'>
              {/* Key metrics */}
              <div className='grid grid-cols-1 md:grid-cols-4 gap-4'>
                <MetricCard
                  title='Running Experiments'
                  value={runningExperiments.length}
                  icon={Play}
                />
                <MetricCard
                  title='Completed Experiments'
                  value={completedExperiments.length}
                  icon={CheckCircle}
                />
                <MetricCard
                  title='Total Sample Size'
                  value={Object.values(analyticsData || {}).reduce(
                    (sum, analytics) => sum + analytics.sample_size,
                    0
                  )}
                  icon={Users}
                />
                <MetricCard
                  title='Significant Results'
                  value={
                    Object.values(analyticsData || {}).filter(
                      a =>
                        a.statistical_significance &&
                        a.statistical_significance > 0.95
                    ).length
                  }
                  icon={Award}
                />
              </div>

              {/* Experiments list */}
              <div className='space-y-4'>
                {experiments.map(experiment => (
                  <ExperimentOverview
                    key={experiment.id}
                    experiment={experiment}
                    analytics={analyticsData?.[experiment.experiment_id]}
                  />
                ))}
              </div>
            </div>
          </TabsContent>

          <TabsContent value='analytics'>
            <div className='space-y-6'>
              {runningExperiments.map(experiment => {
                const analytics = analyticsData?.[experiment.experiment_id];
                if (!analytics) return null;

                return (
                  <Card key={experiment.id}>
                    <CardHeader>
                      <CardTitle>{experiment.name} - Analytics</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className='grid grid-cols-1 md:grid-cols-2 gap-6'>
                        {/* Variant performance */}
                        <div>
                          <h4 className='font-medium mb-3'>
                            Variant Performance
                          </h4>
                          <div className='space-y-3'>
                            {Object.entries(analytics.variants).map(
                              ([variantName, data]) => (
                                <div
                                  key={variantName}
                                  className='border rounded p-3'
                                >
                                  <div className='flex items-center justify-between mb-2'>
                                    <span className='font-medium'>
                                      {variantName}
                                    </span>
                                    <Badge
                                      variant={
                                        variantName === 'control'
                                          ? 'default'
                                          : 'secondary'
                                      }
                                    >
                                      {typeof data.conversion_rate === 'number'
                                        ? data.conversion_rate.toFixed(2)
                                        : '0.00'}
                                      % conversion
                                    </Badge>
                                  </div>
                                  <div className='grid grid-cols-2 gap-2 text-sm text-gray-600'>
                                    <div>Exposures: {data.exposures}</div>
                                    <div>Users: {data.unique_users}</div>
                                  </div>
                                </div>
                              )
                            )}
                          </div>
                        </div>

                        {/* Key metrics */}
                        <div>
                          <h4 className='font-medium mb-3'>Key Metrics</h4>
                          <div className='space-y-2'>
                            <div className='flex justify-between'>
                              <span>Sample Size:</span>
                              <span className='font-medium'>
                                {analytics.sample_size}
                              </span>
                            </div>
                            <div className='flex justify-between'>
                              <span>Statistical Significance:</span>
                              <span className='font-medium'>
                                {analytics.statistical_significance
                                  ? `${(analytics.statistical_significance * 100).toFixed(1)}%`
                                  : 'N/A'}
                              </span>
                            </div>
                            <div className='flex justify-between'>
                              <span>Period:</span>
                              <span className='font-medium'>
                                {new Date(
                                  analytics.period_start
                                ).toLocaleDateString()}{' '}
                                -
                                {new Date(
                                  analytics.period_end
                                ).toLocaleDateString()}
                              </span>
                            </div>
                          </div>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                );
              })}
            </div>
          </TabsContent>

          <TabsContent value='results'>
            <div className='space-y-6'>
              {completedExperiments.length > 0 ? (
                completedExperiments.map(experiment => (
                  <Card key={experiment.id}>
                    <CardHeader>
                      <CardTitle>{experiment.name} - Final Results</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className='space-y-4'>
                        <div className='bg-blue-50 p-4 rounded-lg'>
                          <h4 className='font-medium text-blue-900 mb-2'>
                            Experiment Summary
                          </h4>
                          <p className='text-blue-800 text-sm'>
                            {experiment.description}
                          </p>
                          {experiment.hypothesis && (
                            <p className='text-blue-700 text-sm mt-2'>
                              <strong>Hypothesis:</strong>{' '}
                              {experiment.hypothesis}
                            </p>
                          )}
                        </div>

                        {experiment.results &&
                        Object.keys(experiment.results).length > 0 ? (
                          <div>
                            <h4 className='font-medium mb-2'>Results</h4>
                            <pre className='bg-gray-100 p-3 rounded text-sm'>
                              {JSON.stringify(experiment.results, null, 2)}
                            </pre>
                          </div>
                        ) : (
                          <div className='text-center py-8 text-gray-500'>
                            <BarChart3 className='h-12 w-12 mx-auto mb-4 text-gray-300' />
                            <p>
                              No detailed results available for this experiment
                            </p>
                          </div>
                        )}
                      </div>
                    </CardContent>
                  </Card>
                ))
              ) : (
                <Card>
                  <CardContent className='text-center py-12'>
                    <CheckCircle className='h-12 w-12 mx-auto mb-4 text-gray-300' />
                    <h3 className='text-lg font-medium mb-2'>
                      No completed experiments
                    </h3>
                    <p className='text-gray-600'>
                      Completed experiments will appear here with their final
                      results
                    </p>
                  </CardContent>
                </Card>
              )}
            </div>
          </TabsContent>
        </Tabs>
      )}

      {(!selectedExperiment || experiments.length === 0) && (
        <Card>
          <CardContent className='text-center py-12'>
            <Beaker className='h-12 w-12 mx-auto mb-4 text-gray-300' />
            <h3 className='text-lg font-medium mb-2'>No experiments found</h3>
            <p className='text-gray-600 mb-4'>
              {!selectedExperiment
                ? 'Select an experiment flag to view analytics and results'
                : 'No experiments found for the selected flag'}
            </p>
          </CardContent>
        </Card>
      )}
    </div>
  );
}

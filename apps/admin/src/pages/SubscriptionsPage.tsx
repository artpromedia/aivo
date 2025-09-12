import {
  Plus,
  Search,
  CreditCard,
  AlertCircle,
  CheckCircle,
  XCircle,
  Calendar,
  Users,
} from 'lucide-react';
import { useState } from 'react';

import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Select } from '@/components/ui/select';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import {
  useSubscriptions,
  useSubscriptionPlans,
  useCancelSubscription,
  useReactivateSubscription,
} from '@/hooks/useNewApi';
import { formatCurrency, formatDate } from '@/lib/utils';

export function SubscriptionsPage() {
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('all');

  const { data: subscriptionsData, isLoading } = useSubscriptions({
    page: 1,
    limit: 50,
    status: statusFilter === 'all' ? undefined : statusFilter,
  });

  const { data: plansData } = useSubscriptionPlans();
  const cancelSubscription = useCancelSubscription();
  const reactivateSubscription = useReactivateSubscription();

  const subscriptions = subscriptionsData?.subscriptions || [];
  const plans = plansData?.plans || [];

  const filteredSubscriptions = subscriptions.filter(
    sub =>
      sub.plan_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      sub.tenant_id.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'active':
        return <CheckCircle className='h-4 w-4 text-green-500' />;
      case 'canceled':
        return <XCircle className='h-4 w-4 text-red-500' />;
      case 'past_due':
        return <AlertCircle className='h-4 w-4 text-yellow-500' />;
      case 'trialing':
        return <Calendar className='h-4 w-4 text-blue-500' />;
      default:
        return <AlertCircle className='h-4 w-4 text-gray-500' />;
    }
  };

  const getStatusVariant = (status: string) => {
    switch (status) {
      case 'active':
        return 'default';
      case 'canceled':
        return 'destructive';
      case 'past_due':
        return 'secondary';
      case 'trialing':
        return 'outline';
      default:
        return 'secondary';
    }
  };

  const handleCancelSubscription = async (subscriptionId: string) => {
    if (confirm('Are you sure you want to cancel this subscription?')) {
      await cancelSubscription.mutateAsync({
        subscriptionId,
        cancelAtPeriodEnd: true,
      });
    }
  };

  const handleReactivateSubscription = async (subscriptionId: string) => {
    if (confirm('Are you sure you want to reactivate this subscription?')) {
      await reactivateSubscription.mutateAsync(subscriptionId);
    }
  };

  const activeSubscriptions = subscriptions.filter(
    sub => sub.status === 'active'
  ).length;
  const totalRevenue = subscriptions
    .filter(sub => sub.status === 'active')
    .reduce((sum, sub) => sum + sub.unit_amount * sub.quantity, 0);

  if (isLoading) {
    return (
      <div className='flex items-center justify-center h-64'>
        <div className='text-lg'>Loading subscriptions...</div>
      </div>
    );
  }

  return (
    <div className='space-y-6'>
      {/* Header */}
      <div className='flex items-center justify-between'>
        <div>
          <h1 className='text-3xl font-bold tracking-tight'>
            Subscription Management
          </h1>
          <p className='text-muted-foreground'>
            Manage customer subscriptions, plans, and billing cycles
          </p>
        </div>
        <Button
          onClick={() => alert('Create subscription functionality coming soon')}
        >
          <Plus className='h-4 w-4 mr-2' />
          Create Subscription
        </Button>
      </div>

      {/* Stats Cards */}
      <div className='grid gap-4 md:grid-cols-2 lg:grid-cols-4'>
        <Card>
          <CardHeader className='flex flex-row items-center justify-between space-y-0 pb-2'>
            <CardTitle className='text-sm font-medium'>
              Active Subscriptions
            </CardTitle>
            <CheckCircle className='h-4 w-4 text-muted-foreground' />
          </CardHeader>
          <CardContent>
            <div className='text-2xl font-bold'>{activeSubscriptions}</div>
            <p className='text-xs text-muted-foreground'>
              +12% from last month
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className='flex flex-row items-center justify-between space-y-0 pb-2'>
            <CardTitle className='text-sm font-medium'>
              Monthly Revenue
            </CardTitle>
            <CreditCard className='h-4 w-4 text-muted-foreground' />
          </CardHeader>
          <CardContent>
            <div className='text-2xl font-bold'>
              {formatCurrency(totalRevenue / 100)}
            </div>
            <p className='text-xs text-muted-foreground'>+8% from last month</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className='flex flex-row items-center justify-between space-y-0 pb-2'>
            <CardTitle className='text-sm font-medium'>Total Plans</CardTitle>
            <Users className='h-4 w-4 text-muted-foreground' />
          </CardHeader>
          <CardContent>
            <div className='text-2xl font-bold'>{plans.length}</div>
            <p className='text-xs text-muted-foreground'>
              Available subscription plans
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className='flex flex-row items-center justify-between space-y-0 pb-2'>
            <CardTitle className='text-sm font-medium'>Churn Rate</CardTitle>
            <AlertCircle className='h-4 w-4 text-muted-foreground' />
          </CardHeader>
          <CardContent>
            <div className='text-2xl font-bold'>2.3%</div>
            <p className='text-xs text-muted-foreground'>
              -0.5% from last month
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Filters */}
      <div className='flex items-center space-x-4'>
        <div className='relative flex-1 max-w-sm'>
          <Search className='absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-4 w-4' />
          <Input
            placeholder='Search subscriptions...'
            value={searchTerm}
            onChange={e => setSearchTerm(e.target.value)}
            className='pl-10'
          />
        </div>
        <Select
          value={statusFilter}
          onChange={e => setStatusFilter(e.target.value)}
          className='w-[180px]'
        >
          <option value='all'>All Statuses</option>
          <option value='active'>Active</option>
          <option value='canceled'>Canceled</option>
          <option value='past_due'>Past Due</option>
          <option value='trialing'>Trialing</option>
          <option value='paused'>Paused</option>
        </Select>
      </div>

      {/* Subscriptions Table */}
      <Card>
        <CardHeader>
          <CardTitle>Subscriptions</CardTitle>
          <CardDescription>
            A list of all customer subscriptions and their current status.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Customer</TableHead>
                <TableHead>Plan</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Billing Cycle</TableHead>
                <TableHead>Amount</TableHead>
                <TableHead>Current Period</TableHead>
                <TableHead>Quantity</TableHead>
                <TableHead>Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filteredSubscriptions.map(subscription => (
                <TableRow key={subscription.id}>
                  <TableCell className='font-medium'>
                    {subscription.tenant_id}
                  </TableCell>
                  <TableCell>{subscription.plan_name}</TableCell>
                  <TableCell>
                    <div className='flex items-center space-x-2'>
                      {getStatusIcon(subscription.status)}
                      <Badge variant={getStatusVariant(subscription.status)}>
                        {subscription.status}
                      </Badge>
                    </div>
                  </TableCell>
                  <TableCell className='capitalize'>
                    {subscription.billing_cycle}
                  </TableCell>
                  <TableCell>
                    {formatCurrency(subscription.unit_amount / 100)}
                  </TableCell>
                  <TableCell>
                    <div className='text-sm'>
                      <div>{formatDate(subscription.current_period_start)}</div>
                      <div className='text-muted-foreground'>
                        to {formatDate(subscription.current_period_end)}
                      </div>
                    </div>
                  </TableCell>
                  <TableCell>{subscription.quantity}</TableCell>
                  <TableCell>
                    <div className='flex items-center space-x-2'>
                      {subscription.status === 'active' ? (
                        <Button
                          variant='outline'
                          size='sm'
                          onClick={() =>
                            handleCancelSubscription(subscription.id)
                          }
                          disabled={cancelSubscription.isPending}
                        >
                          Cancel
                        </Button>
                      ) : subscription.status === 'canceled' &&
                        !subscription.cancel_at_period_end ? (
                        <Button
                          variant='outline'
                          size='sm'
                          onClick={() =>
                            handleReactivateSubscription(subscription.id)
                          }
                          disabled={reactivateSubscription.isPending}
                        >
                          Reactivate
                        </Button>
                      ) : null}
                      <Button variant='ghost' size='sm'>
                        Edit
                      </Button>
                    </div>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  );
}

import {
  Download,
  Search,
  FileText,
  CreditCard,
  DollarSign,
  Calendar,
  Filter,
  Eye,
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
  useInvoices,
  useDownloadInvoice,
  usePaymentMethods,
  useUsageMetrics,
} from '@/hooks/useNewApi';
import { formatCurrency, formatDate } from '@/lib/utils';

export function BillingPage() {
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [dateFilter, setDateFilter] = useState<string>('all');
  const [selectedTenant] = useState('current'); // In real app, this would be selected

  const { data: invoicesData, isLoading } = useInvoices({
    page: 1,
    limit: 50,
    status: statusFilter === 'all' ? undefined : statusFilter,
  });

  // const { data: billingHistory } = useBillingHistory(selectedTenant);
  const { data: paymentMethods } = usePaymentMethods(selectedTenant);
  const { data: usageMetrics } = useUsageMetrics(
    selectedTenant,
    'current_month'
  );
  const downloadInvoice = useDownloadInvoice();

  const invoices = invoicesData?.invoices || [];

  const filteredInvoices = invoices.filter(invoice => {
    const matchesSearch =
      invoice.invoice_number.toLowerCase().includes(searchTerm.toLowerCase()) ||
      invoice.description?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      invoice.tenant_id.toLowerCase().includes(searchTerm.toLowerCase());

    const matchesDate =
      dateFilter === 'all' ||
      (dateFilter === 'current_month' &&
        new Date(invoice.created_at).getMonth() === new Date().getMonth()) ||
      (dateFilter === 'last_month' &&
        new Date(invoice.created_at).getMonth() ===
          new Date().getMonth() - 1) ||
      (dateFilter === 'last_3_months' &&
        new Date(invoice.created_at) >=
          new Date(Date.now() - 90 * 24 * 60 * 60 * 1000));

    return matchesSearch && matchesDate;
  });

  const getStatusBadgeVariant = (status: string) => {
    switch (status) {
      case 'paid':
        return 'default';
      case 'open':
        return 'secondary';
      case 'void':
        return 'destructive';
      case 'draft':
        return 'outline';
      case 'uncollectible':
        return 'destructive';
      default:
        return 'secondary';
    }
  };

  const handleDownloadInvoice = async (invoiceId: string) => {
    try {
      await downloadInvoice.mutateAsync(invoiceId);
    } catch {
      alert('Failed to download invoice');
    }
  };

  const totalRevenue = invoices
    .filter(inv => inv.status === 'paid')
    .reduce((sum, inv) => sum + inv.total_amount, 0);

  const pendingAmount = invoices
    .filter(inv => inv.status === 'open')
    .reduce((sum, inv) => sum + inv.total_amount, 0);

  const overdueInvoices = invoices.filter(
    inv => inv.status === 'open' && new Date(inv.due_date) < new Date()
  ).length;

  if (isLoading) {
    return (
      <div className='flex items-center justify-center h-64'>
        <div className='text-lg'>Loading billing data...</div>
      </div>
    );
  }

  return (
    <div className='space-y-6'>
      {/* Header */}
      <div className='flex items-center justify-between'>
        <div>
          <h1 className='text-3xl font-bold tracking-tight'>
            Billing & Invoices
          </h1>
          <p className='text-muted-foreground'>
            Manage invoices, payment methods, and billing history
          </p>
        </div>
        <div className='flex items-center space-x-2'>
          <Button variant='outline'>
            <FileText className='h-4 w-4 mr-2' />
            Generate Report
          </Button>
          <Button>
            <FileText className='h-4 w-4 mr-2' />
            Create Invoice
          </Button>
        </div>
      </div>

      {/* Stats Cards */}
      <div className='grid gap-4 md:grid-cols-2 lg:grid-cols-4'>
        <Card>
          <CardHeader className='flex flex-row items-center justify-between space-y-0 pb-2'>
            <CardTitle className='text-sm font-medium'>Total Revenue</CardTitle>
            <DollarSign className='h-4 w-4 text-muted-foreground' />
          </CardHeader>
          <CardContent>
            <div className='text-2xl font-bold'>
              {formatCurrency(totalRevenue / 100)}
            </div>
            <p className='text-xs text-muted-foreground'>
              +15% from last month
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className='flex flex-row items-center justify-between space-y-0 pb-2'>
            <CardTitle className='text-sm font-medium'>
              Pending Amount
            </CardTitle>
            <Calendar className='h-4 w-4 text-muted-foreground' />
          </CardHeader>
          <CardContent>
            <div className='text-2xl font-bold'>
              {formatCurrency(pendingAmount / 100)}
            </div>
            <p className='text-xs text-muted-foreground'>
              {invoices.filter(inv => inv.status === 'open').length} open
              invoices
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className='flex flex-row items-center justify-between space-y-0 pb-2'>
            <CardTitle className='text-sm font-medium'>
              Overdue Invoices
            </CardTitle>
            <FileText className='h-4 w-4 text-muted-foreground' />
          </CardHeader>
          <CardContent>
            <div className='text-2xl font-bold'>{overdueInvoices}</div>
            <p className='text-xs text-muted-foreground'>
              Require immediate attention
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className='flex flex-row items-center justify-between space-y-0 pb-2'>
            <CardTitle className='text-sm font-medium'>
              Payment Methods
            </CardTitle>
            <CreditCard className='h-4 w-4 text-muted-foreground' />
          </CardHeader>
          <CardContent>
            <div className='text-2xl font-bold'>
              {paymentMethods?.payment_methods?.length || 0}
            </div>
            <p className='text-xs text-muted-foreground'>
              Active payment methods
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Current Usage */}
      {usageMetrics && (
        <Card>
          <CardHeader>
            <CardTitle>Current Month Usage</CardTitle>
            <CardDescription>
              Usage metrics for {formatDate(usageMetrics.period_start)} -{' '}
              {formatDate(usageMetrics.period_end)}
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className='grid gap-4 md:grid-cols-2 lg:grid-cols-4'>
              <div className='space-y-2'>
                <p className='text-sm font-medium'>Active Users</p>
                <p className='text-2xl font-bold'>
                  {usageMetrics.metrics.users_active}
                </p>
              </div>
              <div className='space-y-2'>
                <p className='text-sm font-medium'>Enrolled Devices</p>
                <p className='text-2xl font-bold'>
                  {usageMetrics.metrics.devices_enrolled}
                </p>
              </div>
              <div className='space-y-2'>
                <p className='text-sm font-medium'>Storage Used</p>
                <p className='text-2xl font-bold'>
                  {usageMetrics.metrics.storage_used_gb} GB
                </p>
              </div>
              <div className='space-y-2'>
                <p className='text-sm font-medium'>API Calls</p>
                <p className='text-2xl font-bold'>
                  {usageMetrics.metrics.api_calls.toLocaleString()}
                </p>
              </div>
            </div>
            <div className='mt-4 pt-4 border-t'>
              <div className='flex justify-between items-center'>
                <div>
                  <p className='text-sm text-muted-foreground'>
                    Estimated Month Cost
                  </p>
                  <p className='text-lg font-semibold'>
                    {formatCurrency(usageMetrics.costs.total / 100)}
                  </p>
                </div>
                <div className='text-right'>
                  <p className='text-sm text-muted-foreground'>
                    Overage Charges
                  </p>
                  <p className='text-lg font-semibold'>
                    {formatCurrency(usageMetrics.costs.overage_charges / 100)}
                  </p>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Filters */}
      <div className='flex items-center space-x-4'>
        <div className='relative flex-1 max-w-sm'>
          <Search className='absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-4 w-4' />
          <Input
            placeholder='Search invoices...'
            value={searchTerm}
            onChange={e => setSearchTerm(e.target.value)}
            className='pl-10'
          />
        </div>
        <Select
          value={statusFilter}
          onChange={e => setStatusFilter(e.target.value)}
          className='w-[150px]'
        >
          <option value='all'>All Statuses</option>
          <option value='paid'>Paid</option>
          <option value='open'>Open</option>
          <option value='void'>Void</option>
          <option value='draft'>Draft</option>
          <option value='uncollectible'>Uncollectible</option>
        </Select>
        <Select
          value={dateFilter}
          onChange={e => setDateFilter(e.target.value)}
          className='w-[150px]'
        >
          <option value='all'>All Time</option>
          <option value='current_month'>Current Month</option>
          <option value='last_month'>Last Month</option>
          <option value='last_3_months'>Last 3 Months</option>
        </Select>
        <Button variant='outline' size='sm'>
          <Filter className='h-4 w-4 mr-2' />
          More Filters
        </Button>
      </div>

      {/* Invoices Table */}
      <Card>
        <CardHeader>
          <CardTitle>Invoices</CardTitle>
          <CardDescription>
            A list of all invoices and their payment status.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Invoice</TableHead>
                <TableHead>Customer</TableHead>
                <TableHead>Amount</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Due Date</TableHead>
                <TableHead>Created</TableHead>
                <TableHead>Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filteredInvoices.map(invoice => (
                <TableRow key={invoice.id}>
                  <TableCell className='font-medium'>
                    {invoice.invoice_number}
                  </TableCell>
                  <TableCell>{invoice.tenant_id}</TableCell>
                  <TableCell>
                    {formatCurrency(invoice.total_amount / 100)}
                  </TableCell>
                  <TableCell>
                    <Badge variant={getStatusBadgeVariant(invoice.status)}>
                      {invoice.status}
                    </Badge>
                  </TableCell>
                  <TableCell>
                    <div
                      className={
                        new Date(invoice.due_date) < new Date() &&
                        invoice.status === 'open'
                          ? 'text-red-600'
                          : ''
                      }
                    >
                      {formatDate(invoice.due_date)}
                    </div>
                  </TableCell>
                  <TableCell>{formatDate(invoice.created_at)}</TableCell>
                  <TableCell>
                    <div className='flex items-center space-x-2'>
                      <Button
                        variant='ghost'
                        size='sm'
                        onClick={() =>
                          alert(`View invoice ${invoice.invoice_number}`)
                        }
                      >
                        <Eye className='h-4 w-4' />
                      </Button>
                      {invoice.download_url && (
                        <Button
                          variant='ghost'
                          size='sm'
                          onClick={() => handleDownloadInvoice(invoice.id)}
                          disabled={downloadInvoice.isPending}
                        >
                          <Download className='h-4 w-4' />
                        </Button>
                      )}
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

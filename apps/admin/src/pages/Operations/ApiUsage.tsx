import {
  AlertTriangle,
  Shield,
  TrendingUp,
  Activity,
  Plus,
  Eye,
} from 'lucide-react';
import React, { useState, useEffect } from 'react';

import { Badge } from '../../components/ui/badge';
import { Button } from '../../components/ui/button';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '../../components/ui/card';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '../../components/ui/dialog';
import { Input } from '../../components/ui/input';
import { Label } from '../../components/ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '../../components/ui/select';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '../../components/ui/table';
import {
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
} from '../../components/ui/tabs';
import { Textarea } from '../../components/ui/textarea';

// Types
interface UsageSummary {
  total_requests: number;
  total_tenants: number;
  total_services: number;
  total_routes: number;
  average_response_time: number;
  total_bandwidth_gb: number;
  rate_limited_percentage: number;
  top_services: Array<{ service_name: string; request_count: number }>;
  top_routes: Array<{ route_path: string; request_count: number }>;
  hourly_distribution: Array<{ hour: number; request_count: number }>;
}

interface RateLimit {
  id: string;
  tenant_id: string;
  service_name: string;
  route_pattern: string;
  limit_type: string;
  limit_value: number;
  current_usage: number;
  usage_percentage: number;
  enabled: boolean;
  enforcement_mode: string;
  description?: string;
  created_at: string;
}

interface RateLimitBreach {
  id: string;
  tenant_id: string;
  service_name: string;
  route_path: string;
  breach_timestamp: string;
  attempted_requests: number;
  allowed_limit: number;
  breach_percentage: number;
  action_taken: string;
  resolved: boolean;
}

interface QuotaIncreaseRequest {
  id: string;
  tenant_id: string;
  service_name: string;
  route_pattern: string;
  current_limit: number;
  requested_limit: number;
  limit_type: string;
  justification: string;
  status: 'pending' | 'approved' | 'rejected' | 'implemented';
  requested_by: string;
  requested_at: string;
  reviewed_by?: string;
  reviewed_at?: string;
  rejection_reason?: string;
}

interface LimitsOverview {
  total_rate_limits: number;
  active_rate_limits: number;
  breached_limits_24h: number;
  total_quotas: number;
  quota_warnings: number;
  quota_exceeded: number;
  recent_breaches: RateLimitBreach[];
}

// Form data types
interface QuotaRequestFormData {
  tenant_id: string;
  service_name: string;
  route_pattern: string;
  current_limit: number;
  requested_limit: number;
  limit_type: string;
  justification: string;
  business_impact: string;
  requested_by: string;
  duration_needed: string;
}

interface RateLimitFormData {
  tenant_id: string;
  service_name: string;
  route_pattern: string;
  limit_type: string;
  limit_value: number;
  enforcement_mode: string;
  description: string;
  created_by: string;
}

const API_BASE_URL = 'http://localhost:8500';

export default function ApiUsage() {
  const [usageSummary, setUsageSummary] = useState<UsageSummary | null>(null);
  const [rateLimits, setRateLimits] = useState<RateLimit[]>([]);
  const [breaches, setBreaches] = useState<RateLimitBreach[]>([]);
  const [requests, setRequests] = useState<QuotaIncreaseRequest[]>([]);
  const [limitsOverview, setLimitsOverview] = useState<LimitsOverview | null>(
    null
  );
  const [loading, setLoading] = useState(true);
  const [selectedTab, setSelectedTab] = useState('overview');

  // Filters
  const [tenantFilter, setTenantFilter] = useState('');
  const [serviceFilter, setServiceFilter] = useState('');
  const [dateRange, setDateRange] = useState('30');

  // Modals
  const [isRequestModalOpen, setIsRequestModalOpen] = useState(false);
  const [isCreateLimitModalOpen, setIsCreateLimitModalOpen] = useState(false);
  const [selectedRequest, setSelectedRequest] =
    useState<QuotaIncreaseRequest | null>(null);

  // Fetch data
  useEffect(() => {
    fetchData();
  }, [tenantFilter, serviceFilter, dateRange]);

  // Fetch data with useCallback to fix dependency issue
  const fetchData = React.useCallback(async () => {
    setLoading(true);
    try {
      await Promise.all([
        fetchUsageSummary(),
        fetchRateLimits(),
        fetchBreaches(),
        fetchRequests(),
        fetchLimitsOverview(),
      ]);
    } catch (error) {
      // Error handling - log to console for debugging

      console.error('Error fetching data:', error);
    } finally {
      setLoading(false);
    }
  }, [tenantFilter, serviceFilter, dateRange]);

  const fetchUsageSummary = async () => {
    const params = new URLSearchParams();
    if (tenantFilter) params.append('tenant_id', tenantFilter);
    params.append('range_days', dateRange);

    const response = await fetch(`${API_BASE_URL}/usage/summary?${params}`);
    if (response.ok) {
      const data = await response.json();
      setUsageSummary(data);
    }
  };

  const fetchRateLimits = async () => {
    const params = new URLSearchParams();
    if (tenantFilter) params.append('tenant_id', tenantFilter);
    if (serviceFilter) params.append('service_name', serviceFilter);

    const response = await fetch(
      `${API_BASE_URL}/limits/rate-limits?${params}`
    );
    if (response.ok) {
      const data = await response.json();
      setRateLimits(data);
    }
  };

  const fetchBreaches = async () => {
    const params = new URLSearchParams();
    if (tenantFilter) params.append('tenant_id', tenantFilter);
    if (serviceFilter) params.append('service_name', serviceFilter);

    const response = await fetch(`${API_BASE_URL}/limits/breaches?${params}`);
    if (response.ok) {
      const data = await response.json();
      setBreaches(data);
    }
  };

  const fetchRequests = async () => {
    const params = new URLSearchParams();
    if (tenantFilter) params.append('tenant_id', tenantFilter);
    if (serviceFilter) params.append('service_name', serviceFilter);

    const response = await fetch(`${API_BASE_URL}/requests?${params}`);
    if (response.ok) {
      const data = await response.json();
      setRequests(data);
    }
  };

  const fetchLimitsOverview = async () => {
    const params = new URLSearchParams();
    if (tenantFilter) params.append('tenant_id', tenantFilter);

    const response = await fetch(`${API_BASE_URL}/limits/overview?${params}`);
    if (response.ok) {
      const data = await response.json();
      setLimitsOverview(data);
    }
  };

  const handleCreateQuotaRequest = async (formData: QuotaRequestFormData) => {
    try {
      const response = await fetch(`${API_BASE_URL}/requests`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData),
      });

      if (response.ok) {
        setIsRequestModalOpen(false);
        fetchRequests();
      }
    } catch (error) {
      console.error('Error creating quota request:', error);
    }
  };

  const handleCreateRateLimit = async (formData: RateLimitFormData) => {
    try {
      const response = await fetch(`${API_BASE_URL}/limits/rate-limits`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData),
      });

      if (response.ok) {
        setIsCreateLimitModalOpen(false);
        fetchRateLimits();
      }
    } catch (error) {
      console.error('Error creating rate limit:', error);
    }
  };

  const getStatusBadge = (status: string) => {
    const variants: {
      [key: string]: 'default' | 'secondary' | 'destructive' | 'outline';
    } = {
      pending: 'outline',
      approved: 'default',
      rejected: 'destructive',
      implemented: 'secondary',
    };

    return <Badge variant={variants[status] || 'outline'}>{status}</Badge>;
  };

  if (loading) {
    return (
      <div className='flex items-center justify-center h-64'>
        <div className='animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600'></div>
      </div>
    );
  }

  return (
    <div className='p-6 space-y-6'>
      <div className='flex justify-between items-center'>
        <div>
          <h1 className='text-3xl font-bold'>API Usage & Rate Limits</h1>
          <p className='text-gray-600'>
            Monitor API usage, quotas, and manage rate limits
          </p>
        </div>

        <div className='flex gap-2'>
          <Button onClick={() => setIsCreateLimitModalOpen(true)}>
            <Plus className='h-4 w-4 mr-2' />
            Create Rate Limit
          </Button>
          <Button onClick={() => setIsRequestModalOpen(true)}>
            <TrendingUp className='h-4 w-4 mr-2' />
            Request Quota Increase
          </Button>
        </div>
      </div>

      {/* Filters */}
      <Card>
        <CardHeader>
          <CardTitle>Filters</CardTitle>
        </CardHeader>
        <CardContent>
          <div className='flex gap-4'>
            <div className='flex-1'>
              <Label htmlFor='tenant'>Tenant ID</Label>
              <Input
                id='tenant'
                placeholder='Filter by tenant...'
                value={tenantFilter}
                onChange={e => setTenantFilter(e.target.value)}
              />
            </div>
            <div className='flex-1'>
              <Label htmlFor='service'>Service</Label>
              <Input
                id='service'
                placeholder='Filter by service...'
                value={serviceFilter}
                onChange={e => setServiceFilter(e.target.value)}
              />
            </div>
            <div className='flex-1'>
              <Label htmlFor='range'>Date Range</Label>
              <Select value={dateRange} onValueChange={setDateRange}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value='7'>Last 7 days</SelectItem>
                  <SelectItem value='30'>Last 30 days</SelectItem>
                  <SelectItem value='90'>Last 90 days</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
        </CardContent>
      </Card>

      <Tabs value={selectedTab} onValueChange={setSelectedTab}>
        <TabsList className='grid w-full grid-cols-4'>
          <TabsTrigger value='overview'>Overview</TabsTrigger>
          <TabsTrigger value='limits'>Rate Limits</TabsTrigger>
          <TabsTrigger value='breaches'>Breaches</TabsTrigger>
          <TabsTrigger value='requests'>Quota Requests</TabsTrigger>
        </TabsList>

        <TabsContent value='overview' className='space-y-6'>
          {/* Overview Stats */}
          <div className='grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4'>
            <Card>
              <CardHeader className='flex flex-row items-center justify-between space-y-0 pb-2'>
                <CardTitle className='text-sm font-medium'>
                  Total Requests
                </CardTitle>
                <Activity className='h-4 w-4 text-muted-foreground' />
              </CardHeader>
              <CardContent>
                <div className='text-2xl font-bold'>
                  {usageSummary?.total_requests?.toLocaleString() || 0}
                </div>
                <p className='text-xs text-muted-foreground'>
                  {usageSummary?.total_services || 0} services
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className='flex flex-row items-center justify-between space-y-0 pb-2'>
                <CardTitle className='text-sm font-medium'>
                  Active Limits
                </CardTitle>
                <Shield className='h-4 w-4 text-muted-foreground' />
              </CardHeader>
              <CardContent>
                <div className='text-2xl font-bold'>
                  {limitsOverview?.active_rate_limits || 0}
                </div>
                <p className='text-xs text-muted-foreground'>
                  of {limitsOverview?.total_rate_limits || 0} total
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className='flex flex-row items-center justify-between space-y-0 pb-2'>
                <CardTitle className='text-sm font-medium'>
                  Breaches (24h)
                </CardTitle>
                <AlertTriangle className='h-4 w-4 text-muted-foreground' />
              </CardHeader>
              <CardContent>
                <div className='text-2xl font-bold text-red-600'>
                  {limitsOverview?.breached_limits_24h || 0}
                </div>
                <p className='text-xs text-muted-foreground'>
                  Rate limit violations
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className='flex flex-row items-center justify-between space-y-0 pb-2'>
                <CardTitle className='text-sm font-medium'>Bandwidth</CardTitle>
                <TrendingUp className='h-4 w-4 text-muted-foreground' />
              </CardHeader>
              <CardContent>
                <div className='text-2xl font-bold'>
                  {usageSummary?.total_bandwidth_gb?.toFixed(2) || 0} GB
                </div>
                <p className='text-xs text-muted-foreground'>
                  Avg: {usageSummary?.average_response_time?.toFixed(1) || 0}ms
                </p>
              </CardContent>
            </Card>
          </div>

          {/* Top Services & Routes */}
          <div className='grid grid-cols-1 lg:grid-cols-2 gap-6'>
            <Card>
              <CardHeader>
                <CardTitle>Top Services</CardTitle>
                <CardDescription>
                  Most active services by request count
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className='space-y-2'>
                  {usageSummary?.top_services
                    ?.slice(0, 5)
                    .map((service, index) => (
                      <div
                        key={index}
                        className='flex justify-between items-center'
                      >
                        <span className='text-sm font-medium'>
                          {service.service_name}
                        </span>
                        <span className='text-sm text-gray-600'>
                          {service.request_count.toLocaleString()} requests
                        </span>
                      </div>
                    ))}
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Recent Breaches</CardTitle>
                <CardDescription>Latest rate limit violations</CardDescription>
              </CardHeader>
              <CardContent>
                <div className='space-y-2'>
                  {limitsOverview?.recent_breaches?.slice(0, 5).map(breach => (
                    <div
                      key={breach.id}
                      className='flex justify-between items-center'
                    >
                      <div>
                        <div className='text-sm font-medium'>
                          {breach.service_name}
                        </div>
                        <div className='text-xs text-gray-600'>
                          {breach.route_path}
                        </div>
                      </div>
                      <div className='text-right'>
                        <div className='text-sm'>
                          {breach.attempted_requests}
                        </div>
                        <div className='text-xs text-red-600'>
                          {breach.breach_percentage.toFixed(1)}% over
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value='limits' className='space-y-4'>
          <Card>
            <CardHeader>
              <CardTitle>Rate Limits</CardTitle>
              <CardDescription>
                Manage API rate limits and quotas
              </CardDescription>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Service</TableHead>
                    <TableHead>Route Pattern</TableHead>
                    <TableHead>Limit Type</TableHead>
                    <TableHead>Usage</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Mode</TableHead>
                    <TableHead>Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {rateLimits.map(limit => (
                    <TableRow key={limit.id}>
                      <TableCell className='font-medium'>
                        {limit.service_name}
                      </TableCell>
                      <TableCell>{limit.route_pattern}</TableCell>
                      <TableCell>{limit.limit_type}</TableCell>
                      <TableCell>
                        <div className='flex items-center gap-2'>
                          <div className='flex-1 bg-gray-200 rounded-full h-2'>
                            <div
                              className={`h-2 rounded-full ${
                                limit.usage_percentage > 80
                                  ? 'bg-red-500'
                                  : limit.usage_percentage > 60
                                    ? 'bg-yellow-500'
                                    : 'bg-green-500'
                              }`}
                              style={{
                                width: `${Math.min(limit.usage_percentage, 100)}%`,
                              }}
                            />
                          </div>
                          <span className='text-xs'>
                            {limit.current_usage}/{limit.limit_value}
                          </span>
                        </div>
                      </TableCell>
                      <TableCell>
                        <Badge
                          variant={limit.enabled ? 'default' : 'secondary'}
                        >
                          {limit.enabled ? 'Active' : 'Disabled'}
                        </Badge>
                      </TableCell>
                      <TableCell>{limit.enforcement_mode}</TableCell>
                      <TableCell>
                        <Button variant='outline' size='sm'>
                          <Eye className='h-4 w-4' />
                        </Button>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value='breaches' className='space-y-4'>
          <Card>
            <CardHeader>
              <CardTitle>Rate Limit Breaches</CardTitle>
              <CardDescription>
                Recent violations with timestamps
              </CardDescription>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Timestamp</TableHead>
                    <TableHead>Service</TableHead>
                    <TableHead>Route</TableHead>
                    <TableHead>Attempted</TableHead>
                    <TableHead>Limit</TableHead>
                    <TableHead>Breach %</TableHead>
                    <TableHead>Action</TableHead>
                    <TableHead>Status</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {breaches.map(breach => (
                    <TableRow key={breach.id}>
                      <TableCell>
                        {new Date(breach.breach_timestamp).toLocaleString()}
                      </TableCell>
                      <TableCell className='font-medium'>
                        {breach.service_name}
                      </TableCell>
                      <TableCell>{breach.route_path}</TableCell>
                      <TableCell>{breach.attempted_requests}</TableCell>
                      <TableCell>{breach.allowed_limit}</TableCell>
                      <TableCell>
                        <span className='text-red-600 font-medium'>
                          +{breach.breach_percentage.toFixed(1)}%
                        </span>
                      </TableCell>
                      <TableCell>{breach.action_taken}</TableCell>
                      <TableCell>
                        <Badge
                          variant={breach.resolved ? 'default' : 'destructive'}
                        >
                          {breach.resolved ? 'Resolved' : 'Open'}
                        </Badge>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value='requests' className='space-y-4'>
          <Card>
            <CardHeader>
              <CardTitle>Quota Increase Requests</CardTitle>
              <CardDescription>
                Submit and track quota increase requests
              </CardDescription>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Service</TableHead>
                    <TableHead>Route</TableHead>
                    <TableHead>Current → Requested</TableHead>
                    <TableHead>Type</TableHead>
                    <TableHead>Requested By</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Date</TableHead>
                    <TableHead>Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {requests.map(request => (
                    <TableRow key={request.id}>
                      <TableCell className='font-medium'>
                        {request.service_name}
                      </TableCell>
                      <TableCell>{request.route_pattern}</TableCell>
                      <TableCell>
                        {request.current_limit} → {request.requested_limit}
                      </TableCell>
                      <TableCell>{request.limit_type}</TableCell>
                      <TableCell>{request.requested_by}</TableCell>
                      <TableCell>{getStatusBadge(request.status)}</TableCell>
                      <TableCell>
                        {new Date(request.requested_at).toLocaleDateString()}
                      </TableCell>
                      <TableCell>
                        <Button
                          variant='outline'
                          size='sm'
                          onClick={() => setSelectedRequest(request)}
                        >
                          <Eye className='h-4 w-4' />
                        </Button>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* Quota Request Modal */}
      <QuotaRequestModal
        isOpen={isRequestModalOpen}
        onClose={() => setIsRequestModalOpen(false)}
        onSubmit={handleCreateQuotaRequest}
      />

      {/* Rate Limit Modal */}
      <RateLimitModal
        isOpen={isCreateLimitModalOpen}
        onClose={() => setIsCreateLimitModalOpen(false)}
        onSubmit={handleCreateRateLimit}
      />

      {/* Request Details Modal */}
      {selectedRequest && (
        <RequestDetailsModal
          request={selectedRequest}
          isOpen={!!selectedRequest}
          onClose={() => setSelectedRequest(null)}
        />
      )}
    </div>
  );
}

// Modal Components
function QuotaRequestModal({
  isOpen,
  onClose,
  onSubmit,
}: {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (data: QuotaRequestFormData) => void;
}) {
  const [formData, setFormData] = useState({
    tenant_id: '',
    service_name: '',
    route_pattern: '',
    current_limit: 0,
    requested_limit: 0,
    limit_type: 'requests_per_hour',
    justification: '',
    business_impact: '',
    requested_by: 'admin',
    duration_needed: 'permanent',
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSubmit(formData);
  };

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className='max-w-2xl'>
        <DialogHeader>
          <DialogTitle>Request Quota Increase</DialogTitle>
          <DialogDescription>
            Submit a request to increase API quotas or rate limits
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit} className='space-y-4'>
          <div className='grid grid-cols-2 gap-4'>
            <div>
              <Label htmlFor='tenant_id'>Tenant ID</Label>
              <Input
                id='tenant_id'
                value={formData.tenant_id}
                onChange={e =>
                  setFormData({ ...formData, tenant_id: e.target.value })
                }
                required
              />
            </div>
            <div>
              <Label htmlFor='service_name'>Service Name</Label>
              <Input
                id='service_name'
                value={formData.service_name}
                onChange={e =>
                  setFormData({ ...formData, service_name: e.target.value })
                }
                required
              />
            </div>
          </div>

          <div>
            <Label htmlFor='route_pattern'>Route Pattern</Label>
            <Input
              id='route_pattern'
              placeholder='/api/v1/secrets/*'
              value={formData.route_pattern}
              onChange={e =>
                setFormData({ ...formData, route_pattern: e.target.value })
              }
              required
            />
          </div>

          <div className='grid grid-cols-3 gap-4'>
            <div>
              <Label htmlFor='current_limit'>Current Limit</Label>
              <Input
                id='current_limit'
                type='number'
                value={formData.current_limit}
                onChange={e =>
                  setFormData({
                    ...formData,
                    current_limit: parseInt(e.target.value),
                  })
                }
                required
              />
            </div>
            <div>
              <Label htmlFor='requested_limit'>Requested Limit</Label>
              <Input
                id='requested_limit'
                type='number'
                value={formData.requested_limit}
                onChange={e =>
                  setFormData({
                    ...formData,
                    requested_limit: parseInt(e.target.value),
                  })
                }
                required
              />
            </div>
            <div>
              <Label htmlFor='limit_type'>Limit Type</Label>
              <Select
                value={formData.limit_type}
                onValueChange={value =>
                  setFormData({ ...formData, limit_type: value })
                }
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value='requests_per_minute'>
                    Requests/Minute
                  </SelectItem>
                  <SelectItem value='requests_per_hour'>
                    Requests/Hour
                  </SelectItem>
                  <SelectItem value='requests_per_day'>Requests/Day</SelectItem>
                  <SelectItem value='requests_per_month'>
                    Requests/Month
                  </SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>

          <div>
            <Label htmlFor='justification'>Business Justification</Label>
            <Textarea
              id='justification'
              placeholder='Explain why this increase is needed...'
              value={formData.justification}
              onChange={e =>
                setFormData({ ...formData, justification: e.target.value })
              }
              required
            />
          </div>

          <div>
            <Label htmlFor='business_impact'>Business Impact</Label>
            <Textarea
              id='business_impact'
              placeholder='Describe the business impact if not approved...'
              value={formData.business_impact}
              onChange={e =>
                setFormData({ ...formData, business_impact: e.target.value })
              }
            />
          </div>

          <DialogFooter>
            <Button type='button' variant='outline' onClick={onClose}>
              Cancel
            </Button>
            <Button type='submit'>Submit Request</Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}

function RateLimitModal({
  isOpen,
  onClose,
  onSubmit,
}: {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (data: RateLimitFormData) => void;
}) {
  const [formData, setFormData] = useState({
    tenant_id: '',
    service_name: '',
    route_pattern: '',
    limit_type: 'requests_per_hour',
    limit_value: 100,
    enforcement_mode: 'enforce',
    description: '',
    created_by: 'admin',
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSubmit(formData);
  };

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Create Rate Limit</DialogTitle>
          <DialogDescription>
            Set up a new rate limit for API endpoints
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit} className='space-y-4'>
          <div className='grid grid-cols-2 gap-4'>
            <div>
              <Label htmlFor='tenant_id'>Tenant ID</Label>
              <Input
                id='tenant_id'
                value={formData.tenant_id}
                onChange={e =>
                  setFormData({ ...formData, tenant_id: e.target.value })
                }
                required
              />
            </div>
            <div>
              <Label htmlFor='service_name'>Service Name</Label>
              <Input
                id='service_name'
                value={formData.service_name}
                onChange={e =>
                  setFormData({ ...formData, service_name: e.target.value })
                }
                required
              />
            </div>
          </div>

          <div>
            <Label htmlFor='route_pattern'>Route Pattern</Label>
            <Input
              id='route_pattern'
              placeholder='/api/v1/secrets/*'
              value={formData.route_pattern}
              onChange={e =>
                setFormData({ ...formData, route_pattern: e.target.value })
              }
              required
            />
          </div>

          <div className='grid grid-cols-2 gap-4'>
            <div>
              <Label htmlFor='limit_type'>Limit Type</Label>
              <Select
                value={formData.limit_type}
                onValueChange={value =>
                  setFormData({ ...formData, limit_type: value })
                }
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value='requests_per_minute'>
                    Requests/Minute
                  </SelectItem>
                  <SelectItem value='requests_per_hour'>
                    Requests/Hour
                  </SelectItem>
                  <SelectItem value='requests_per_day'>Requests/Day</SelectItem>
                  <SelectItem value='requests_per_month'>
                    Requests/Month
                  </SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div>
              <Label htmlFor='limit_value'>Limit Value</Label>
              <Input
                id='limit_value'
                type='number'
                value={formData.limit_value}
                onChange={e =>
                  setFormData({
                    ...formData,
                    limit_value: parseInt(e.target.value),
                  })
                }
                required
              />
            </div>
          </div>

          <div>
            <Label htmlFor='enforcement_mode'>Enforcement Mode</Label>
            <Select
              value={formData.enforcement_mode}
              onValueChange={value =>
                setFormData({ ...formData, enforcement_mode: value })
              }
            >
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value='enforce'>Enforce</SelectItem>
                <SelectItem value='warn'>Warn Only</SelectItem>
                <SelectItem value='monitor'>Monitor Only</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <div>
            <Label htmlFor='description'>Description</Label>
            <Textarea
              id='description'
              placeholder='Optional description...'
              value={formData.description}
              onChange={e =>
                setFormData({ ...formData, description: e.target.value })
              }
            />
          </div>

          <DialogFooter>
            <Button type='button' variant='outline' onClick={onClose}>
              Cancel
            </Button>
            <Button type='submit'>Create Limit</Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}

function RequestDetailsModal({
  request,
  isOpen,
  onClose,
}: {
  request: QuotaIncreaseRequest;
  isOpen: boolean;
  onClose: () => void;
}) {
  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className='max-w-2xl'>
        <DialogHeader>
          <DialogTitle>Quota Request Details</DialogTitle>
          <DialogDescription>Request ID: {request.id}</DialogDescription>
        </DialogHeader>

        <div className='space-y-4'>
          <div className='grid grid-cols-2 gap-4'>
            <div>
              <Label>Service</Label>
              <p className='text-sm'>{request.service_name}</p>
            </div>
            <div>
              <Label>Route Pattern</Label>
              <p className='text-sm'>{request.route_pattern}</p>
            </div>
          </div>

          <div className='grid grid-cols-3 gap-4'>
            <div>
              <Label>Current Limit</Label>
              <p className='text-sm'>{request.current_limit}</p>
            </div>
            <div>
              <Label>Requested Limit</Label>
              <p className='text-sm'>{request.requested_limit}</p>
            </div>
            <div>
              <Label>Status</Label>
              <p className='text-sm'>{getStatusBadge(request.status)}</p>
            </div>
          </div>

          <div>
            <Label>Justification</Label>
            <p className='text-sm bg-gray-50 p-3 rounded'>
              {request.justification}
            </p>
          </div>

          {request.rejection_reason && (
            <div>
              <Label>Rejection Reason</Label>
              <p className='text-sm bg-red-50 p-3 rounded text-red-700'>
                {request.rejection_reason}
              </p>
            </div>
          )}

          <div className='grid grid-cols-2 gap-4'>
            <div>
              <Label>Requested By</Label>
              <p className='text-sm'>{request.requested_by}</p>
            </div>
            <div>
              <Label>Requested At</Label>
              <p className='text-sm'>
                {new Date(request.requested_at).toLocaleString()}
              </p>
            </div>
          </div>

          {request.reviewed_by && (
            <div className='grid grid-cols-2 gap-4'>
              <div>
                <Label>Reviewed By</Label>
                <p className='text-sm'>{request.reviewed_by}</p>
              </div>
              <div>
                <Label>Reviewed At</Label>
                <p className='text-sm'>
                  {request.reviewed_at
                    ? new Date(request.reviewed_at).toLocaleString()
                    : 'N/A'}
                </p>
              </div>
            </div>
          )}
        </div>

        <DialogFooter>
          <Button onClick={onClose}>Close</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

function getStatusBadge(status: string) {
  const variants: {
    [key: string]: 'default' | 'secondary' | 'destructive' | 'outline';
  } = {
    pending: 'outline',
    approved: 'default',
    rejected: 'destructive',
    implemented: 'secondary',
  };

  return <Badge variant={variants[status] || 'outline'}>{status}</Badge>;
}

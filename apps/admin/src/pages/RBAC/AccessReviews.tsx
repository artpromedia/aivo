import {
  Plus,
  CheckCircle,
  X,
  Eye,
  Calendar,
  AlertTriangle,
  RefreshCw,
  AlertCircle,
  Filter,
  ChevronRight,
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
import { Label } from '@/components/ui/label';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import {
  useAccessReviews,
  useCreateAccessReview,
  useReviewItems,
  useSubmitReviewDecision,
} from '@/hooks/useRBAC';

interface AccessReviewsProps {
  tenantId?: string;
}

interface ReviewFormData {
  title: string;
  description: string;
  scope: 'admin' | 'all_users' | 'role_specific';
  targetRoleId?: string;
  dueDays: number;
}

interface AccessReviewSummary {
  total: number;
  active: number;
  completed: number;
  overdue: number;
}

interface AccessReview {
  id: string;
  title: string;
  description?: string;
  scope: string;
  status: string;
  progress_percentage: number;
  reviewed_items: number;
  total_items: number;
  due_date: string;
  days_remaining?: number;
  urgency_level: string;
}

interface ReviewItem {
  id: string;
  user_name: string;
  user_id: string;
  role_name: string;
  role_privileges: string[];
  formatted_last_access: string;
  risk_level: string;
  status: string;
}

interface AccessReviewsData {
  reviews: AccessReview[];
  summary: AccessReviewSummary;
}

interface ReviewItemsData {
  items: ReviewItem[];
  summary: Record<string, unknown>;
}

export default function AccessReviews({ tenantId }: AccessReviewsProps) {
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [selectedReview, setSelectedReview] = useState<string | null>(null);
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [reviewFormData, setReviewFormData] = useState<ReviewFormData>({
    title: '',
    description: '',
    scope: 'admin',
    dueDays: 30,
  });
  const [reviewDecision, setReviewDecision] = useState<{
    itemId: string;
    decision: string;
    notes: string;
    justification: string;
  } | null>(null);
  const [errors, setErrors] = useState<Record<string, string>>({});

  // API hooks
  const {
    data: reviewsData,
    isLoading: reviewsLoading,
    refetch: refetchReviews,
  } = useAccessReviews(
    tenantId,
    statusFilter === 'all' ? undefined : statusFilter
  ) as {
    data: { data: AccessReviewsData } | undefined;
    isLoading: boolean;
    refetch: () => void;
  };
  const { data: reviewItemsData, isLoading: itemsLoading } = useReviewItems(
    selectedReview || '',
    tenantId
  ) as {
    data: { data: ReviewItemsData } | undefined;
    isLoading: boolean;
  };

  const createReviewMutation = useCreateAccessReview();
  const submitDecisionMutation = useSubmitReviewDecision();

  const handleCreateReview = async () => {
    setErrors({});

    // Validation
    if (!reviewFormData.title.trim()) {
      setErrors(prev => ({ ...prev, title: 'Review title is required' }));
      return;
    }

    try {
      await createReviewMutation.mutateAsync({
        title: reviewFormData.title,
        description: reviewFormData.description,
        tenantId,
        scope: reviewFormData.scope,
        targetRoleId: reviewFormData.targetRoleId,
        dueDays: reviewFormData.dueDays,
      });

      // Reset form
      setReviewFormData({
        title: '',
        description: '',
        scope: 'admin',
        dueDays: 30,
      });
      setShowCreateForm(false);

      await refetchReviews();
       
    } catch (error) {
      setErrors({ form: 'Failed to create access review. Please try again.' });
    }
  };

  const handleSubmitDecision = async () => {
    if (!reviewDecision || !selectedReview) return;

    try {
      await submitDecisionMutation.mutateAsync({
        reviewId: selectedReview,
        itemId: reviewDecision.itemId,
        decision: reviewDecision.decision,
        notes: reviewDecision.notes,
        justification: reviewDecision.justification,
        tenantId,
      });

      setReviewDecision(null);
      // Refetch review items to update the list
       
    } catch (error) {
      setErrors({ decision: 'Failed to submit decision. Please try again.' });
    }
  };

  const getUrgencyColor = (urgencyLevel: string) => {
    switch (urgencyLevel) {
      case 'critical':
        return 'text-red-600 bg-red-100';
      case 'high':
        return 'text-orange-600 bg-orange-100';
      case 'medium':
        return 'text-yellow-600 bg-yellow-100';
      default:
        return 'text-green-600 bg-green-100';
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed':
        return 'text-green-600 bg-green-100';
      case 'active':
        return 'text-blue-600 bg-blue-100';
      case 'draft':
        return 'text-gray-600 bg-gray-100';
      default:
        return 'text-gray-600 bg-gray-100';
    }
  };

  if (reviewsLoading) {
    return (
      <div className='flex items-center justify-center min-h-[400px]'>
        <RefreshCw className='h-8 w-8 animate-spin text-blue-600' />
        <span className='ml-2 text-gray-600'>Loading access reviews...</span>
      </div>
    );
  }

  const reviews = reviewsData?.data.reviews || [];
  const reviewItems = reviewItemsData?.data.items || [];

  return (
    <div className='space-y-6'>
      {/* Header */}
      <div className='flex items-center justify-between'>
        <div>
          <h1 className='text-3xl font-bold text-gray-900 flex items-center'>
            <CheckCircle className='h-8 w-8 mr-3 text-blue-600' />
            Access Reviews
          </h1>
          <p className='text-gray-600 mt-1'>
            Quarterly access certification and audit workflows
          </p>
        </div>

        <Button
          onClick={() => setShowCreateForm(true)}
          disabled={showCreateForm}
        >
          <Plus className='h-4 w-4 mr-2' />
          Start Review
        </Button>
      </div>

      {/* Error Alert */}
      {(errors.form || errors.decision) && (
        <Card className='border-red-200 bg-red-50'>
          <CardContent className='pt-6'>
            <div className='flex items-center text-red-700'>
              <AlertCircle className='h-5 w-5 mr-2' />
              <span>{errors.form || errors.decision}</span>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Summary Stats */}
      <div className='grid grid-cols-1 md:grid-cols-4 gap-4'>
        <Card>
          <CardContent className='pt-6'>
            <div className='flex items-center'>
              <Calendar className='h-8 w-8 text-blue-600' />
              <div className='ml-4'>
                <p className='text-sm font-medium text-gray-600'>
                  Total Reviews
                </p>
                <p className='text-2xl font-bold'>
                  {reviewsData?.data.summary.total || 0}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className='pt-6'>
            <div className='flex items-center'>
              <RefreshCw className='h-8 w-8 text-green-600' />
              <div className='ml-4'>
                <p className='text-sm font-medium text-gray-600'>Active</p>
                <p className='text-2xl font-bold'>
                  {reviewsData?.data.summary.active || 0}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className='pt-6'>
            <div className='flex items-center'>
              <CheckCircle className='h-8 w-8 text-green-600' />
              <div className='ml-4'>
                <p className='text-sm font-medium text-gray-600'>Completed</p>
                <p className='text-2xl font-bold'>
                  {reviewsData?.data.summary.completed || 0}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className='pt-6'>
            <div className='flex items-center'>
              <AlertTriangle className='h-8 w-8 text-red-600' />
              <div className='ml-4'>
                <p className='text-sm font-medium text-gray-600'>Overdue</p>
                <p className='text-2xl font-bold'>
                  {reviewsData?.data.summary.overdue || 0}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Create Review Form */}
      {showCreateForm && (
        <Card>
          <CardHeader>
            <CardTitle>Start New Access Review</CardTitle>
            <CardDescription>
              Create a new quarterly access certification review
            </CardDescription>
          </CardHeader>
          <CardContent className='space-y-6'>
            <div className='space-y-2'>
              <Label htmlFor='review-title'>Review Title</Label>
              <Input
                id='review-title'
                value={reviewFormData.title}
                onChange={e =>
                  setReviewFormData(prev => ({
                    ...prev,
                    title: e.target.value,
                  }))
                }
                placeholder='e.g., Q1 2024 Access Review'
                className={errors.title ? 'border-red-500' : ''}
              />
              {errors.title && (
                <p className='text-sm text-red-600'>{errors.title}</p>
              )}
            </div>

            <div className='space-y-2'>
              <Label htmlFor='description'>Description (Optional)</Label>
              <Input
                id='description'
                value={reviewFormData.description}
                onChange={e =>
                  setReviewFormData(prev => ({
                    ...prev,
                    description: e.target.value,
                  }))
                }
                placeholder='Brief description of the review scope and purpose'
              />
            </div>

            <div className='grid grid-cols-1 md:grid-cols-2 gap-4'>
              <div className='space-y-2'>
                <Label htmlFor='scope'>Review Scope</Label>
                <select
                  id='scope'
                  className='flex h-10 w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500'
                  value={reviewFormData.scope}
                  onChange={e =>
                    setReviewFormData(prev => ({
                      ...prev,
                      scope: e.target.value as
                        | 'admin'
                        | 'all_users'
                        | 'role_specific',
                    }))
                  }
                >
                  <option value='admin'>Admin Users Only</option>
                  <option value='all_users'>All Users</option>
                  <option value='role_specific'>Specific Role</option>
                </select>
              </div>

              <div className='space-y-2'>
                <Label htmlFor='due-days'>Due in Days</Label>
                <Input
                  id='due-days'
                  type='number'
                  min='1'
                  max='365'
                  value={reviewFormData.dueDays}
                  onChange={e =>
                    setReviewFormData(prev => ({
                      ...prev,
                      dueDays: parseInt(e.target.value) || 30,
                    }))
                  }
                />
              </div>
            </div>

            <div className='flex justify-end space-x-2'>
              <Button
                variant='outline'
                onClick={() => setShowCreateForm(false)}
              >
                <X className='h-4 w-4 mr-2' />
                Cancel
              </Button>
              <Button
                onClick={handleCreateReview}
                disabled={createReviewMutation.isPending}
              >
                <Calendar className='h-4 w-4 mr-2' />
                {createReviewMutation.isPending
                  ? 'Creating...'
                  : 'Start Review'}
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Filters */}
      <Card>
        <CardHeader>
          <CardTitle className='flex items-center'>
            <Filter className='h-5 w-5 mr-2' />
            Filters
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className='flex items-center space-x-4'>
            <div className='flex items-center space-x-2'>
              <Label htmlFor='status-filter'>Status:</Label>
              <select
                id='status-filter'
                className='flex h-10 w-[150px] rounded-md border border-gray-300 bg-white px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500'
                value={statusFilter}
                onChange={e => setStatusFilter(e.target.value)}
              >
                <option value='all'>All Statuses</option>
                <option value='active'>Active</option>
                <option value='completed'>Completed</option>
                <option value='draft'>Draft</option>
              </select>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Reviews List or Review Details */}
      {selectedReview ? (
        <Card>
          <CardHeader>
            <div className='flex items-center justify-between'>
              <CardTitle>Review Items</CardTitle>
              <Button variant='outline' onClick={() => setSelectedReview(null)}>
                <ChevronRight className='h-4 w-4 mr-2 rotate-180' />
                Back to Reviews
              </Button>
            </div>
            <CardDescription>
              Review and approve or revoke user access
            </CardDescription>
          </CardHeader>
          <CardContent>
            {itemsLoading ? (
              <div className='flex items-center justify-center py-8'>
                <RefreshCw className='h-6 w-6 animate-spin text-blue-600' />
                <span className='ml-2'>Loading review items...</span>
              </div>
            ) : (
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>User</TableHead>
                    <TableHead>Role</TableHead>
                    <TableHead>Last Access</TableHead>
                    <TableHead>Risk Level</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {reviewItems.map((item: ReviewItem) => (
                    <TableRow key={item.id}>
                      <TableCell>
                        <div>
                          <div className='font-medium'>{item.user_name}</div>
                          <div className='text-sm text-gray-500'>
                            {item.user_id}
                          </div>
                        </div>
                      </TableCell>
                      <TableCell>
                        <div>
                          <div className='font-medium'>{item.role_name}</div>
                          <div className='text-xs text-gray-500'>
                            {item.role_privileges.join(', ')}
                          </div>
                        </div>
                      </TableCell>
                      <TableCell>
                        <span className='text-sm'>
                          {item.formatted_last_access}
                        </span>
                      </TableCell>
                      <TableCell>
                        <Badge className={getUrgencyColor(item.risk_level)}>
                          {item.risk_level}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        <Badge className={getStatusColor(item.status)}>
                          {item.status}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        {item.status === 'pending' && (
                          <div className='flex space-x-1'>
                            <Button
                              size='sm'
                              variant='outline'
                              onClick={() =>
                                setReviewDecision({
                                  itemId: item.id,
                                  decision: 'approve',
                                  notes: '',
                                  justification: '',
                                })
                              }
                              className='text-green-600 hover:text-green-700'
                            >
                              <CheckCircle className='h-4 w-4' />
                            </Button>
                            <Button
                              size='sm'
                              variant='outline'
                              onClick={() =>
                                setReviewDecision({
                                  itemId: item.id,
                                  decision: 'revoke',
                                  notes: '',
                                  justification: '',
                                })
                              }
                              className='text-red-600 hover:text-red-700'
                            >
                              <X className='h-4 w-4' />
                            </Button>
                          </div>
                        )}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            )}
          </CardContent>
        </Card>
      ) : (
        <Card>
          <CardHeader>
            <CardTitle>Access Reviews</CardTitle>
            <CardDescription>
              Manage ongoing and completed access certification reviews
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Review</TableHead>
                  <TableHead>Scope</TableHead>
                  <TableHead>Progress</TableHead>
                  <TableHead>Due Date</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Urgency</TableHead>
                  <TableHead>Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {reviews.map((review: AccessReview) => (
                  <TableRow key={review.id}>
                    <TableCell>
                      <div>
                        <div className='font-medium'>{review.title}</div>
                        <div className='text-sm text-gray-500'>
                          {review.description}
                        </div>
                      </div>
                    </TableCell>
                    <TableCell>
                      <span className='capitalize'>
                        {review.scope.replace('_', ' ')}
                      </span>
                    </TableCell>
                    <TableCell>
                      <div className='space-y-1'>
                        <div className='flex justify-between text-sm'>
                          <span>
                            {review.reviewed_items}/{review.total_items}
                          </span>
                          <span>{review.progress_percentage}%</span>
                        </div>
                        <div className='w-full bg-gray-200 rounded-full h-2'>
                          <div
                            className='bg-blue-600 h-2 rounded-full'
                            style={{ width: `${review.progress_percentage}%` }}
                          ></div>
                        </div>
                      </div>
                    </TableCell>
                    <TableCell>
                      <div>
                        <div className='text-sm'>
                          {new Date(review.due_date).toLocaleDateString()}
                        </div>
                        {review.days_remaining !== null &&
                          review.days_remaining !== undefined && (
                            <div className='text-xs text-gray-500'>
                              {review.days_remaining > 0
                                ? `${review.days_remaining} days left`
                                : 'Overdue'}
                            </div>
                          )}
                      </div>
                    </TableCell>
                    <TableCell>
                      <Badge className={getStatusColor(review.status)}>
                        {review.status}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      <Badge className={getUrgencyColor(review.urgency_level)}>
                        {review.urgency_level}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      <div className='flex space-x-1'>
                        <Button
                          size='sm'
                          variant='outline'
                          onClick={() => setSelectedReview(review.id)}
                        >
                          <Eye className='h-4 w-4' />
                        </Button>
                      </div>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      )}

      {/* Decision Modal */}
      {reviewDecision && (
        <Card className='fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50'>
          <div className='bg-white rounded-lg p-6 max-w-md w-full mx-4'>
            <h3 className='text-lg font-semibold mb-4'>
              {reviewDecision.decision === 'approve'
                ? 'Approve Access'
                : 'Revoke Access'}
            </h3>

            <div className='space-y-4'>
              <div>
                <Label htmlFor='decision-notes'>Notes</Label>
                <Input
                  id='decision-notes'
                  value={reviewDecision.notes}
                  onChange={e =>
                    setReviewDecision(prev =>
                      prev ? { ...prev, notes: e.target.value } : null
                    )
                  }
                  placeholder='Optional notes'
                />
              </div>

              <div>
                <Label htmlFor='decision-justification'>Justification</Label>
                <Input
                  id='decision-justification'
                  value={reviewDecision.justification}
                  onChange={e =>
                    setReviewDecision(prev =>
                      prev ? { ...prev, justification: e.target.value } : null
                    )
                  }
                  placeholder='Reason for this decision'
                />
              </div>
            </div>

            <div className='flex justify-end space-x-2 mt-6'>
              <Button variant='outline' onClick={() => setReviewDecision(null)}>
                Cancel
              </Button>
              <Button
                onClick={handleSubmitDecision}
                disabled={submitDecisionMutation.isPending}
                className={
                  reviewDecision.decision === 'approve'
                    ? 'bg-green-600 hover:bg-green-700'
                    : 'bg-red-600 hover:bg-red-700'
                }
              >
                {submitDecisionMutation.isPending
                  ? 'Submitting...'
                  : `${reviewDecision.decision === 'approve' ? 'Approve' : 'Revoke'} Access`}
              </Button>
            </div>
          </div>
        </Card>
      )}
    </div>
  );
}

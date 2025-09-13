import {
  Clock,
  MessageSquare,
  AlertTriangle,
  CheckCircle,
  Plus,
  Search,
  ExternalLink,
  RefreshCw,
} from 'lucide-react';
import { useState, useEffect, useCallback } from 'react';

import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { Textarea } from '@/components/ui/textarea';

interface Ticket {
  id: number;
  title: string;
  description: string;
  status: 'open' | 'in_progress' | 'resolved' | 'closed';
  priority: 'low' | 'medium' | 'high' | 'critical';
  tenant_id: string;
  created_by: string;
  assigned_to?: string;
  created_at: string;
  updated_at: string;
  resolved_at?: string;
  sla_deadline?: string;
  sla_status: 'on_time' | 'at_risk' | 'breached';
  first_response_at?: string;
  incident_id?: string;
}

interface TicketComment {
  id: number;
  ticket_id: number;
  comment: string;
  created_by: string;
  created_at: string;
  is_internal: boolean;
}

interface TicketStats {
  total_tickets: number;
  open_tickets: number;
  in_progress_tickets: number;
  resolved_tickets: number;
  sla_breached: number;
  avg_resolution_time_hours: number;
  tickets_by_priority: Record<string, number>;
}

interface NewTicketData {
  title: string;
  description: string;
  priority: 'low' | 'medium' | 'high' | 'critical';
  tenant_id: string;
  created_by: string;
  assigned_to?: string;
  incident_id?: string;
}

interface NewCommentData {
  comment: string;
  created_by: string;
  is_internal: boolean;
}

const SUPPORT_API_BASE = 'http://localhost:8510';

const statusColors = {
  open: 'bg-blue-100 text-blue-800',
  in_progress: 'bg-yellow-100 text-yellow-800',
  resolved: 'bg-green-100 text-green-800',
  closed: 'bg-gray-100 text-gray-800',
};

const priorityColors = {
  low: 'bg-gray-100 text-gray-800',
  medium: 'bg-blue-100 text-blue-800',
  high: 'bg-orange-100 text-orange-800',
  critical: 'bg-red-100 text-red-800',
};

const slaColors = {
  on_time: 'bg-green-100 text-green-800',
  at_risk: 'bg-yellow-100 text-yellow-800',
  breached: 'bg-red-100 text-red-800',
};

export default function Tickets() {
  const [tickets, setTickets] = useState<Ticket[]>([]);
  const [stats, setStats] = useState<TicketStats | null>(null);
  const [selectedTicket, setSelectedTicket] = useState<Ticket | null>(null);
  const [comments, setComments] = useState<TicketComment[]>([]);
  const [loading, setLoading] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [priorityFilter, setPriorityFilter] = useState<string>('all');
  const [showNewTicketDialog, setShowNewTicketDialog] = useState(false);
  const [showTicketDialog, setShowTicketDialog] = useState(false);
  const [newTicket, setNewTicket] = useState<NewTicketData>({
    title: '',
    description: '',
    priority: 'medium',
    tenant_id: '',
    created_by: 'admin',
    assigned_to: '',
    incident_id: '',
  });
  const [newComment, setNewComment] = useState<NewCommentData>({
    comment: '',
    created_by: 'admin',
    is_internal: false,
  });

  const fetchTickets = useCallback(async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (statusFilter !== 'all') params.append('status', statusFilter);
      if (priorityFilter !== 'all') params.append('priority', priorityFilter);

      const response = await fetch(`${SUPPORT_API_BASE}/tickets?${params}`);
      if (response.ok) {
        const data = await response.json();
        setTickets(data);
      }
    } catch {
      // Handle error silently
    } finally {
      setLoading(false);
    }
  }, [statusFilter, priorityFilter]);

  const fetchStats = async () => {
    try {
      const response = await fetch(
        `${SUPPORT_API_BASE}/tickets/stats/overview`
      );
      if (response.ok) {
        const data = await response.json();
        setStats(data);
      }
    } catch {
      // Handle error silently
    }
  };

  const fetchComments = async (ticketId: number) => {
    try {
      const response = await fetch(
        `${SUPPORT_API_BASE}/tickets/${ticketId}/comments`
      );
      if (response.ok) {
        const data = await response.json();
        setComments(data);
      }
    } catch {
      // Handle error silently
    }
  };

  const createTicket = async () => {
    if (!newTicket.title || !newTicket.description || !newTicket.tenant_id)
      return;

    try {
      const response = await fetch(`${SUPPORT_API_BASE}/tickets`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(newTicket),
      });

      if (response.ok) {
        setNewTicket({
          title: '',
          description: '',
          priority: 'medium',
          tenant_id: '',
          created_by: 'admin',
          assigned_to: '',
          incident_id: '',
        });
        setShowNewTicketDialog(false);
        fetchTickets();
        fetchStats();
      }
    } catch {
      // Handle error silently
    }
  };

  const updateTicketStatus = async (ticketId: number, status: string) => {
    try {
      const response = await fetch(`${SUPPORT_API_BASE}/tickets/${ticketId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ status }),
      });

      if (response.ok) {
        fetchTickets();
        fetchStats();
        if (selectedTicket?.id === ticketId) {
          const updatedTicket = await response.json();
          setSelectedTicket(updatedTicket);
        }
      }
    } catch {
      // Handle error silently
    }
  };

  const addComment = async () => {
    if (!selectedTicket || !newComment.comment) return;

    try {
      const response = await fetch(
        `${SUPPORT_API_BASE}/tickets/${selectedTicket.id}/comment`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(newComment),
        }
      );

      if (response.ok) {
        setNewComment({
          comment: '',
          created_by: 'admin',
          is_internal: false,
        });
        fetchComments(selectedTicket.id);
      }
    } catch {
      // Handle error silently
    }
  };

  const formatDateTime = (dateString: string) => {
    return new Date(dateString).toLocaleString();
  };

  const formatTimeUntilDeadline = (deadline: string) => {
    const now = new Date();
    const deadlineDate = new Date(deadline);
    const diff = deadlineDate.getTime() - now.getTime();

    if (diff < 0) return 'Overdue';

    const hours = Math.floor(diff / (1000 * 60 * 60));
    const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));

    if (hours > 24) {
      const days = Math.floor(hours / 24);
      return `${days}d ${hours % 24}h`;
    }

    return `${hours}h ${minutes}m`;
  };

  const openTicketDialog = (ticket: Ticket) => {
    setSelectedTicket(ticket);
    fetchComments(ticket.id);
    setShowTicketDialog(true);
  };

  useEffect(() => {
    fetchTickets();
    fetchStats();
  }, [fetchTickets]);

  const filteredTickets = tickets.filter(
    ticket =>
      ticket.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
      ticket.description.toLowerCase().includes(searchTerm.toLowerCase()) ||
      ticket.tenant_id.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div className='space-y-6'>
      {/* Header */}
      <div className='flex justify-between items-center'>
        <div>
          <h1 className='text-3xl font-bold'>Support Tickets</h1>
          <p className='text-gray-600'>
            Manage support tickets and track SLA compliance
          </p>
        </div>
        <div className='flex gap-2'>
          <Button onClick={fetchTickets} variant='outline' size='sm'>
            <RefreshCw className='h-4 w-4 mr-2' />
            Refresh
          </Button>
          <Dialog
            open={showNewTicketDialog}
            onOpenChange={setShowNewTicketDialog}
          >
            <DialogTrigger>
              <Button>
                <Plus className='h-4 w-4 mr-2' />
                New Ticket
              </Button>
            </DialogTrigger>
            <DialogContent className='max-w-md'>
              <DialogHeader>
                <DialogTitle>Create New Ticket</DialogTitle>
              </DialogHeader>
              <div className='space-y-4'>
                <Input
                  placeholder='Ticket title'
                  value={newTicket.title}
                  onChange={e =>
                    setNewTicket({ ...newTicket, title: e.target.value })
                  }
                />
                <Textarea
                  placeholder='Description'
                  value={newTicket.description}
                  onChange={e =>
                    setNewTicket({ ...newTicket, description: e.target.value })
                  }
                />
                <Input
                  placeholder='Tenant ID'
                  value={newTicket.tenant_id}
                  onChange={e =>
                    setNewTicket({ ...newTicket, tenant_id: e.target.value })
                  }
                />
                <Select
                  value={newTicket.priority}
                  onValueChange={value =>
                    setNewTicket({
                      ...newTicket,
                      priority: value as 'low' | 'medium' | 'high' | 'critical',
                    })
                  }
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value='low'>Low</SelectItem>
                    <SelectItem value='medium'>Medium</SelectItem>
                    <SelectItem value='high'>High</SelectItem>
                    <SelectItem value='critical'>Critical</SelectItem>
                  </SelectContent>
                </Select>
                <Input
                  placeholder='Assigned to (optional)'
                  value={newTicket.assigned_to}
                  onChange={e =>
                    setNewTicket({ ...newTicket, assigned_to: e.target.value })
                  }
                />
                <Input
                  placeholder='Incident ID (optional)'
                  value={newTicket.incident_id}
                  onChange={e =>
                    setNewTicket({ ...newTicket, incident_id: e.target.value })
                  }
                />
                <Button onClick={createTicket} className='w-full'>
                  Create Ticket
                </Button>
              </div>
            </DialogContent>
          </Dialog>
        </div>
      </div>

      {/* Stats */}
      {stats && (
        <div className='grid grid-cols-1 md:grid-cols-4 gap-4'>
          <div className='bg-white p-6 rounded-lg border shadow-sm'>
            <div className='flex items-center justify-between'>
              <div>
                <p className='text-sm text-gray-600'>Total Tickets</p>
                <p className='text-2xl font-bold'>{stats.total_tickets}</p>
              </div>
              <MessageSquare className='h-8 w-8 text-blue-500' />
            </div>
          </div>
          <div className='bg-white p-6 rounded-lg border shadow-sm'>
            <div className='flex items-center justify-between'>
              <div>
                <p className='text-sm text-gray-600'>Open Tickets</p>
                <p className='text-2xl font-bold'>{stats.open_tickets}</p>
              </div>
              <AlertTriangle className='h-8 w-8 text-orange-500' />
            </div>
          </div>
          <div className='bg-white p-6 rounded-lg border shadow-sm'>
            <div className='flex items-center justify-between'>
              <div>
                <p className='text-sm text-gray-600'>SLA Breached</p>
                <p className='text-2xl font-bold'>{stats.sla_breached}</p>
              </div>
              <Clock className='h-8 w-8 text-red-500' />
            </div>
          </div>
          <div className='bg-white p-6 rounded-lg border shadow-sm'>
            <div className='flex items-center justify-between'>
              <div>
                <p className='text-sm text-gray-600'>Avg Resolution (hrs)</p>
                <p className='text-2xl font-bold'>
                  {stats.avg_resolution_time_hours.toFixed(1)}
                </p>
              </div>
              <CheckCircle className='h-8 w-8 text-green-500' />
            </div>
          </div>
        </div>
      )}

      {/* Filters */}
      <div className='bg-white p-4 rounded-lg border shadow-sm'>
        <div className='flex flex-wrap gap-4'>
          <div className='flex items-center gap-2'>
            <Search className='h-4 w-4 text-gray-500' />
            <Input
              placeholder='Search tickets...'
              value={searchTerm}
              onChange={e => setSearchTerm(e.target.value)}
              className='w-64'
            />
          </div>
          <Select value={statusFilter} onValueChange={setStatusFilter}>
            <SelectTrigger className='w-40'>
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value='all'>All Status</SelectItem>
              <SelectItem value='open'>Open</SelectItem>
              <SelectItem value='in_progress'>In Progress</SelectItem>
              <SelectItem value='resolved'>Resolved</SelectItem>
              <SelectItem value='closed'>Closed</SelectItem>
            </SelectContent>
          </Select>
          <Select value={priorityFilter} onValueChange={setPriorityFilter}>
            <SelectTrigger className='w-40'>
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value='all'>All Priority</SelectItem>
              <SelectItem value='low'>Low</SelectItem>
              <SelectItem value='medium'>Medium</SelectItem>
              <SelectItem value='high'>High</SelectItem>
              <SelectItem value='critical'>Critical</SelectItem>
            </SelectContent>
          </Select>
        </div>
      </div>

      {/* Tickets Table */}
      <div className='bg-white rounded-lg border shadow-sm'>
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>ID</TableHead>
              <TableHead>Title</TableHead>
              <TableHead>Status</TableHead>
              <TableHead>Priority</TableHead>
              <TableHead>SLA Status</TableHead>
              <TableHead>SLA Deadline</TableHead>
              <TableHead>Tenant</TableHead>
              <TableHead>Assigned To</TableHead>
              <TableHead>Created</TableHead>
              <TableHead>Actions</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {loading ? (
              <TableRow>
                <TableCell colSpan={10} className='text-center py-8'>
                  Loading tickets...
                </TableCell>
              </TableRow>
            ) : filteredTickets.length === 0 ? (
              <TableRow>
                <TableCell
                  colSpan={10}
                  className='text-center py-8 text-gray-500'
                >
                  No tickets found
                </TableCell>
              </TableRow>
            ) : (
              filteredTickets.map(ticket => (
                <TableRow
                  key={ticket.id}
                  className='cursor-pointer hover:bg-gray-50'
                  onClick={() => openTicketDialog(ticket)}
                >
                  <TableCell className='font-medium'>#{ticket.id}</TableCell>
                  <TableCell className='max-w-xs truncate'>
                    {ticket.title}
                  </TableCell>
                  <TableCell>
                    <Badge className={statusColors[ticket.status]}>
                      {ticket.status.replace('_', ' ')}
                    </Badge>
                  </TableCell>
                  <TableCell>
                    <Badge className={priorityColors[ticket.priority]}>
                      {ticket.priority}
                    </Badge>
                  </TableCell>
                  <TableCell>
                    <Badge className={slaColors[ticket.sla_status]}>
                      {ticket.sla_status.replace('_', ' ')}
                    </Badge>
                  </TableCell>
                  <TableCell>
                    {ticket.sla_deadline ? (
                      <span
                        className={
                          ticket.sla_status === 'breached' ? 'text-red-600' : ''
                        }
                      >
                        {formatTimeUntilDeadline(ticket.sla_deadline)}
                      </span>
                    ) : (
                      '-'
                    )}
                  </TableCell>
                  <TableCell>{ticket.tenant_id}</TableCell>
                  <TableCell>{ticket.assigned_to || '-'}</TableCell>
                  <TableCell>{formatDateTime(ticket.created_at)}</TableCell>
                  <TableCell>
                    <div className='flex gap-1'>
                      {ticket.status !== 'resolved' && (
                        <Button
                          size='sm'
                          variant='outline'
                          onClick={e => {
                            e.stopPropagation();
                            updateTicketStatus(ticket.id, 'resolved');
                          }}
                        >
                          Resolve
                        </Button>
                      )}
                      {ticket.incident_id && (
                        <Button size='sm' variant='ghost'>
                          <ExternalLink className='h-4 w-4' />
                        </Button>
                      )}
                    </div>
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </div>

      {/* Ticket Detail Dialog */}
      <Dialog open={showTicketDialog} onOpenChange={setShowTicketDialog}>
        <DialogContent className='max-w-4xl max-h-[90vh] overflow-y-auto'>
          {selectedTicket && (
            <>
              <DialogHeader>
                <DialogTitle className='flex items-center gap-2'>
                  <span>
                    Ticket #{selectedTicket.id}: {selectedTicket.title}
                  </span>
                  <Badge className={statusColors[selectedTicket.status]}>
                    {selectedTicket.status.replace('_', ' ')}
                  </Badge>
                  <Badge className={priorityColors[selectedTicket.priority]}>
                    {selectedTicket.priority}
                  </Badge>
                </DialogTitle>
              </DialogHeader>

              <div className='space-y-6'>
                {/* Ticket Info */}
                <div className='grid grid-cols-2 gap-4 p-4 bg-gray-50 rounded-lg'>
                  <div>
                    <p className='text-sm text-gray-600'>Created by</p>
                    <p className='font-medium'>{selectedTicket.created_by}</p>
                  </div>
                  <div>
                    <p className='text-sm text-gray-600'>Tenant ID</p>
                    <p className='font-medium'>{selectedTicket.tenant_id}</p>
                  </div>
                  <div>
                    <p className='text-sm text-gray-600'>Created at</p>
                    <p className='font-medium'>
                      {formatDateTime(selectedTicket.created_at)}
                    </p>
                  </div>
                  <div>
                    <p className='text-sm text-gray-600'>SLA Status</p>
                    <Badge className={slaColors[selectedTicket.sla_status]}>
                      {selectedTicket.sla_status.replace('_', ' ')}
                    </Badge>
                  </div>
                  {selectedTicket.sla_deadline && (
                    <div>
                      <p className='text-sm text-gray-600'>SLA Deadline</p>
                      <p className='font-medium'>
                        {formatTimeUntilDeadline(selectedTicket.sla_deadline)}
                      </p>
                    </div>
                  )}
                  {selectedTicket.incident_id && (
                    <div>
                      <p className='text-sm text-gray-600'>Linked Incident</p>
                      <p className='font-medium'>
                        {selectedTicket.incident_id}
                      </p>
                    </div>
                  )}
                </div>

                {/* Description */}
                <div>
                  <h3 className='text-lg font-semibold mb-2'>Description</h3>
                  <p className='text-gray-700 whitespace-pre-wrap'>
                    {selectedTicket.description}
                  </p>
                </div>

                {/* Status Actions */}
                <div className='flex gap-2'>
                  <Button
                    onClick={() =>
                      updateTicketStatus(selectedTicket.id, 'in_progress')
                    }
                    disabled={selectedTicket.status === 'in_progress'}
                    variant='outline'
                  >
                    Mark In Progress
                  </Button>
                  <Button
                    onClick={() =>
                      updateTicketStatus(selectedTicket.id, 'resolved')
                    }
                    disabled={selectedTicket.status === 'resolved'}
                    variant='outline'
                  >
                    Mark Resolved
                  </Button>
                </div>

                {/* Comments */}
                <div>
                  <h3 className='text-lg font-semibold mb-4'>Comments</h3>
                  <div className='space-y-4 max-h-64 overflow-y-auto'>
                    {comments.map(comment => (
                      <div
                        key={comment.id}
                        className={`p-3 rounded-lg ${
                          comment.is_internal
                            ? 'bg-yellow-50 border-yellow-200'
                            : 'bg-blue-50 border-blue-200'
                        } border`}
                      >
                        <div className='flex justify-between items-start mb-2'>
                          <span className='font-medium'>
                            {comment.created_by}
                          </span>
                          <div className='flex items-center gap-2'>
                            {comment.is_internal && (
                              <Badge variant='secondary'>Internal</Badge>
                            )}
                            <span className='text-sm text-gray-500'>
                              {formatDateTime(comment.created_at)}
                            </span>
                          </div>
                        </div>
                        <p className='text-gray-700 whitespace-pre-wrap'>
                          {comment.comment}
                        </p>
                      </div>
                    ))}
                  </div>

                  {/* Add Comment */}
                  <div className='mt-4 space-y-3'>
                    <Textarea
                      placeholder='Add a comment...'
                      value={newComment.comment}
                      onChange={e =>
                        setNewComment({
                          ...newComment,
                          comment: e.target.value,
                        })
                      }
                    />
                    <div className='flex justify-between items-center'>
                      <label className='flex items-center gap-2'>
                        <input
                          type='checkbox'
                          checked={newComment.is_internal}
                          onChange={e =>
                            setNewComment({
                              ...newComment,
                              is_internal: e.target.checked,
                            })
                          }
                        />
                        <span className='text-sm'>Internal comment</span>
                      </label>
                      <Button
                        onClick={addComment}
                        disabled={!newComment.comment}
                      >
                        Add Comment
                      </Button>
                    </div>
                  </div>
                </div>
              </div>
            </>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}

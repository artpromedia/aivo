import { Users, UserPlus, Shield, UserX, Search } from 'lucide-react';
import { useState } from 'react';

import { Button } from '@/components/ui/button';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { useUsers, useUpdateUserRole, useDeactivateUser } from '@/hooks/useApi';
import { formatDateTime } from '@/lib/utils';

interface User {
  id: string;
  username: string;
  email: string;
  role: string;
  status: string;
  lastLogin: string;
  createdAt: string;
}

export function UsersPage() {
  const [currentPage, setCurrentPage] = useState(1);
  const [searchTerm, setSearchTerm] = useState('');

  const { data: usersData, isLoading } = useUsers(currentPage, 10);
  const updateRoleMutation = useUpdateUserRole();
  const deactivateUserMutation = useDeactivateUser();

  const handleRoleChange = async (userId: string, newRole: string) => {
    try {
      await updateRoleMutation.mutateAsync({ userId, role: newRole });
      alert('User role updated successfully!');
    } catch {
      // TODO: Implement proper error logging
      alert('Failed to update user role');
    }
  };

  const handleDeactivateUser = async (userId: string) => {
    if (confirm('Are you sure you want to deactivate this user?')) {
      try {
        await deactivateUserMutation.mutateAsync(userId);
        alert('User deactivated successfully!');
      } catch {
        // TODO: Implement proper error logging
        alert('Failed to deactivate user');
      }
    }
  };

  const handleInviteUser = () => {
    // Open invite user modal/form
    alert('Invite user functionality - would open modal with form');
  };

  const handleSearchUsers = () => {
    // TODO: Implement search functionality
    if (searchTerm) {
      // Search logic will be implemented here
    }
  };

  const filteredUsers = usersData?.users || [];

  return (
    <div className='space-y-6'>
      {/* Header */}
      <div className='flex justify-between items-center'>
        <div>
          <h1 className='text-3xl font-bold tracking-tight'>
            Users & Licenses
          </h1>
          <p className='text-muted-foreground'>
            Manage user accounts, roles, and license assignments
          </p>
        </div>
        <Button onClick={handleInviteUser}>
          <UserPlus className='h-4 w-4 mr-2' />
          Invite User
        </Button>
      </div>

      {/* Summary Cards */}
      <div className='grid gap-4 md:grid-cols-3'>
        <Card>
          <CardHeader className='flex flex-row items-center justify-between space-y-0 pb-2'>
            <CardTitle className='text-sm font-medium'>Total Users</CardTitle>
            <Users className='h-4 w-4 text-muted-foreground' />
          </CardHeader>
          <CardContent>
            <div className='text-2xl font-bold'>{usersData?.total || 0}</div>
            <p className='text-xs text-muted-foreground'>Across all roles</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className='flex flex-row items-center justify-between space-y-0 pb-2'>
            <CardTitle className='text-sm font-medium'>
              Active Licenses
            </CardTitle>
            <Shield className='h-4 w-4 text-muted-foreground' />
          </CardHeader>
          <CardContent>
            <div className='text-2xl font-bold'>78</div>
            <p className='text-xs text-muted-foreground'>
              Out of 100 available
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className='flex flex-row items-center justify-between space-y-0 pb-2'>
            <CardTitle className='text-sm font-medium'>
              Pending Invites
            </CardTitle>
            <UserPlus className='h-4 w-4 text-muted-foreground' />
          </CardHeader>
          <CardContent>
            <div className='text-2xl font-bold'>5</div>
            <p className='text-xs text-muted-foreground'>Awaiting acceptance</p>
          </CardContent>
        </Card>
      </div>

      {/* Search and Filters */}
      <Card>
        <CardHeader>
          <CardTitle>User Management</CardTitle>
          <CardDescription>Search and manage user accounts</CardDescription>
        </CardHeader>
        <CardContent>
          <div className='flex gap-4 mb-6'>
            <div className='flex-1 relative'>
              <Search className='absolute left-3 top-3 h-4 w-4 text-muted-foreground' />
              <input
                type='text'
                placeholder='Search users by name or email...'
                value={searchTerm}
                onChange={e => setSearchTerm(e.target.value)}
                onKeyPress={e => e.key === 'Enter' && handleSearchUsers()}
                className='w-full pl-10 pr-4 py-2 border border-input rounded-md bg-background text-sm'
              />
            </div>
            <Button onClick={handleSearchUsers} variant='outline'>
              Search
            </Button>
          </div>

          {/* Users Table */}
          <div className='border rounded-lg'>
            <div className='grid grid-cols-12 gap-4 p-4 font-medium text-sm bg-muted'>
              <div className='col-span-3'>User</div>
              <div className='col-span-2'>Role</div>
              <div className='col-span-2'>Status</div>
              <div className='col-span-2'>Last Login</div>
              <div className='col-span-2'>Created</div>
              <div className='col-span-1'>Actions</div>
            </div>

            {isLoading ? (
              <div className='p-8 text-center text-muted-foreground'>
                Loading users...
              </div>
            ) : filteredUsers.length === 0 ? (
              <div className='p-8 text-center text-muted-foreground'>
                No users found
              </div>
            ) : (
              filteredUsers.map((user: User) => (
                <div
                  key={user.id}
                  className='grid grid-cols-12 gap-4 p-4 border-t items-center'
                >
                  <div className='col-span-3'>
                    <div className='flex items-center gap-3'>
                      <div className='w-8 h-8 bg-primary rounded-full flex items-center justify-center text-primary-foreground text-sm font-medium'>
                        {user.username.charAt(0).toUpperCase()}
                      </div>
                      <div>
                        <p className='font-medium text-sm'>{user.username}</p>
                        <p className='text-xs text-muted-foreground'>
                          {user.email}
                        </p>
                      </div>
                    </div>
                  </div>

                  <div className='col-span-2'>
                    <select
                      value={user.role}
                      onChange={e => handleRoleChange(user.id, e.target.value)}
                      className='text-sm border border-input rounded px-2 py-1 bg-background'
                    >
                      <option value='user'>User</option>
                      <option value='staff'>Staff</option>
                      <option value='district_admin'>District Admin</option>
                      <option value='system_admin'>System Admin</option>
                    </select>
                  </div>

                  <div className='col-span-2'>
                    <span
                      className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${
                        user.status === 'active'
                          ? 'bg-green-100 text-green-800'
                          : 'bg-red-100 text-red-800'
                      }`}
                    >
                      {user.status}
                    </span>
                  </div>

                  <div className='col-span-2 text-sm text-muted-foreground'>
                    {formatDateTime(user.lastLogin)}
                  </div>

                  <div className='col-span-2 text-sm text-muted-foreground'>
                    {formatDateTime(user.createdAt)}
                  </div>

                  <div className='col-span-1'>
                    <Button
                      variant='ghost'
                      size='sm'
                      onClick={() => handleDeactivateUser(user.id)}
                      className='h-8 w-8 p-0'
                    >
                      <UserX className='h-4 w-4' />
                    </Button>
                  </div>
                </div>
              ))
            )}
          </div>

          {/* Pagination */}
          {usersData && usersData.totalPages > 1 && (
            <div className='flex justify-between items-center mt-4'>
              <p className='text-sm text-muted-foreground'>
                Page {usersData.page} of {usersData.totalPages}
              </p>
              <div className='flex gap-2'>
                <Button
                  variant='outline'
                  size='sm'
                  onClick={() => setCurrentPage(prev => Math.max(1, prev - 1))}
                  disabled={currentPage === 1}
                >
                  Previous
                </Button>
                <Button
                  variant='outline'
                  size='sm'
                  onClick={() =>
                    setCurrentPage(prev =>
                      Math.min(usersData.totalPages, prev + 1)
                    )
                  }
                  disabled={currentPage === usersData.totalPages}
                >
                  Next
                </Button>
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

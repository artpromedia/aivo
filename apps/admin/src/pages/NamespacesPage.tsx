import {
  Plus,
  Search,
  FolderTree,
  Settings,
  Trash2,
  Edit,
  Users,
  Shield,
  BarChart3,
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
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import {
  useNamespaces,
  useNamespaceTree,
  useDeleteNamespace,
} from '@/hooks/useNewApi';
import { formatDate } from '@/lib/utils';

export function NamespacesPage() {
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedNamespace, setSelectedNamespace] = useState<string | null>(
    null
  );

  const { data: namespacesData, isLoading } = useNamespaces({
    page: 1,
    limit: 100,
    include_children: true,
  });

  const { data: treeData } = useNamespaceTree();
  const deleteNamespace = useDeleteNamespace();

  const namespaces = namespacesData?.namespaces || [];
  const tree = treeData?.tree || [];

  const filteredNamespaces = namespaces.filter(
    namespace =>
      namespace.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      namespace.description.toLowerCase().includes(searchTerm.toLowerCase()) ||
      namespace.path.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const handleDeleteNamespace = async (
    namespaceId: string,
    namespaceName: string
  ) => {
    if (
      confirm(
        `Are you sure you want to delete namespace "${namespaceName}"? This action cannot be undone.`
      )
    ) {
      try {
        await deleteNamespace.mutateAsync({ namespaceId, force: false });
      } catch {
        if (
          confirm(
            'This namespace contains devices or child namespaces. Force delete?'
          )
        ) {
          await deleteNamespace.mutateAsync({ namespaceId, force: true });
        }
      }
    }
  };

  const getStatusBadge = (isActive: boolean) => {
    return (
      <Badge variant={isActive ? 'default' : 'secondary'}>
        {isActive ? 'Active' : 'Inactive'}
      </Badge>
    );
  };

  interface TreeNode {
    id: string;
    name: string;
    device_count: number;
    children?: TreeNode[];
  }

  const renderTreeNode = (node: TreeNode, level = 0) => {
    return (
      <div key={node.id} className='space-y-1'>
        <div
          className={`flex items-center space-x-2 p-2 rounded cursor-pointer hover:bg-gray-50 ${
            selectedNamespace === node.id
              ? 'bg-blue-50 border border-blue-200'
              : ''
          }`}
          style={{ marginLeft: level * 20 }}
          onClick={() => setSelectedNamespace(node.id)}
        >
          <FolderTree className='h-4 w-4 text-gray-500' />
          <span className='font-medium'>{node.name}</span>
          <span className='text-sm text-gray-500'>
            ({node.device_count} devices)
          </span>
        </div>
        {node.children?.map((child: TreeNode) =>
          renderTreeNode(child, level + 1)
        )}
      </div>
    );
  };

  const totalNamespaces = namespaces.length;
  const totalDevices = namespaces.reduce((sum, ns) => sum + ns.device_count, 0);
  const averageDevicesPerNamespace =
    totalNamespaces > 0 ? Math.round(totalDevices / totalNamespaces) : 0;
  const activeNamespaces = namespaces.filter(ns => ns.is_active).length;

  if (isLoading) {
    return (
      <div className='flex items-center justify-center h-64'>
        <div className='text-lg'>Loading namespaces...</div>
      </div>
    );
  }

  return (
    <div className='space-y-6'>
      {/* Header */}
      <div className='flex items-center justify-between'>
        <div>
          <h1 className='text-3xl font-bold tracking-tight'>
            Device Namespaces
          </h1>
          <p className='text-muted-foreground'>
            Organize and manage device hierarchies and policies
          </p>
        </div>
        <Button
          onClick={() => alert('Create namespace functionality coming soon')}
        >
          <Plus className='h-4 w-4 mr-2' />
          Create Namespace
        </Button>
      </div>

      {/* Stats Cards */}
      <div className='grid gap-4 md:grid-cols-2 lg:grid-cols-4'>
        <Card>
          <CardHeader className='flex flex-row items-center justify-between space-y-0 pb-2'>
            <CardTitle className='text-sm font-medium'>
              Total Namespaces
            </CardTitle>
            <FolderTree className='h-4 w-4 text-muted-foreground' />
          </CardHeader>
          <CardContent>
            <div className='text-2xl font-bold'>{totalNamespaces}</div>
            <p className='text-xs text-muted-foreground'>
              {activeNamespaces} active
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className='flex flex-row items-center justify-between space-y-0 pb-2'>
            <CardTitle className='text-sm font-medium'>Total Devices</CardTitle>
            <Users className='h-4 w-4 text-muted-foreground' />
          </CardHeader>
          <CardContent>
            <div className='text-2xl font-bold'>{totalDevices}</div>
            <p className='text-xs text-muted-foreground'>
              Across all namespaces
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className='flex flex-row items-center justify-between space-y-0 pb-2'>
            <CardTitle className='text-sm font-medium'>
              Avg Devices/Namespace
            </CardTitle>
            <BarChart3 className='h-4 w-4 text-muted-foreground' />
          </CardHeader>
          <CardContent>
            <div className='text-2xl font-bold'>
              {averageDevicesPerNamespace}
            </div>
            <p className='text-xs text-muted-foreground'>
              Average distribution
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className='flex flex-row items-center justify-between space-y-0 pb-2'>
            <CardTitle className='text-sm font-medium'>
              Applied Policies
            </CardTitle>
            <Shield className='h-4 w-4 text-muted-foreground' />
          </CardHeader>
          <CardContent>
            <div className='text-2xl font-bold'>
              {namespaces.reduce((sum, ns) => sum + ns.policy_count, 0)}
            </div>
            <p className='text-xs text-muted-foreground'>
              Total policy assignments
            </p>
          </CardContent>
        </Card>
      </div>

      <div className='grid gap-6 lg:grid-cols-3'>
        {/* Namespace Tree */}
        <Card className='lg:col-span-1'>
          <CardHeader>
            <CardTitle>Namespace Hierarchy</CardTitle>
            <CardDescription>
              Visual representation of namespace structure
            </CardDescription>
          </CardHeader>
          <CardContent className='space-y-2 max-h-96 overflow-y-auto'>
            {tree.length > 0 ? (
              tree.map(node => renderTreeNode(node))
            ) : (
              <div className='text-center text-gray-500 py-8'>
                No namespaces found
              </div>
            )}
          </CardContent>
        </Card>

        {/* Namespace Table */}
        <Card className='lg:col-span-2'>
          <CardHeader>
            <CardTitle>All Namespaces</CardTitle>
            <CardDescription>
              Detailed list of all device namespaces
            </CardDescription>
            <div className='relative'>
              <Search className='absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-4 w-4' />
              <Input
                placeholder='Search namespaces...'
                value={searchTerm}
                onChange={e => setSearchTerm(e.target.value)}
                className='pl-10'
              />
            </div>
          </CardHeader>
          <CardContent>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Name</TableHead>
                  <TableHead>Path</TableHead>
                  <TableHead>Devices</TableHead>
                  <TableHead>Policies</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Created</TableHead>
                  <TableHead>Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filteredNamespaces.map(namespace => (
                  <TableRow
                    key={namespace.id}
                    className={
                      selectedNamespace === namespace.id ? 'bg-blue-50' : ''
                    }
                  >
                    <TableCell className='font-medium'>
                      <div>
                        <div>{namespace.name}</div>
                        {namespace.description && (
                          <div className='text-sm text-gray-500 truncate max-w-32'>
                            {namespace.description}
                          </div>
                        )}
                      </div>
                    </TableCell>
                    <TableCell className='font-mono text-sm'>
                      {namespace.path}
                    </TableCell>
                    <TableCell>
                      <Badge variant='outline'>{namespace.device_count}</Badge>
                    </TableCell>
                    <TableCell>
                      <Badge variant='outline'>{namespace.policy_count}</Badge>
                    </TableCell>
                    <TableCell>{getStatusBadge(namespace.is_active)}</TableCell>
                    <TableCell>{formatDate(namespace.created_at)}</TableCell>
                    <TableCell>
                      <div className='flex items-center space-x-2'>
                        <Button
                          variant='ghost'
                          size='sm'
                          onClick={() =>
                            alert(`Edit namespace ${namespace.name}`)
                          }
                        >
                          <Edit className='h-4 w-4' />
                        </Button>
                        <Button
                          variant='ghost'
                          size='sm'
                          onClick={() =>
                            alert(`Configure namespace ${namespace.name}`)
                          }
                        >
                          <Settings className='h-4 w-4' />
                        </Button>
                        <Button
                          variant='ghost'
                          size='sm'
                          onClick={() =>
                            handleDeleteNamespace(namespace.id, namespace.name)
                          }
                          disabled={deleteNamespace.isPending}
                        >
                          <Trash2 className='h-4 w-4' />
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

      {/* Selected Namespace Details */}
      {selectedNamespace && (
        <Card>
          <CardHeader>
            <CardTitle>Namespace Details</CardTitle>
            <CardDescription>
              Detailed information about the selected namespace
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className='text-center text-gray-500 py-8'>
              Select a namespace from the hierarchy or table to view details
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}

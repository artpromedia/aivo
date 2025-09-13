import {
  BookOpen,
  Plus,
  Search,
  Edit,
  Trash2,
  Eye,
  ExternalLink,
  RefreshCw,
  Tag,
  Globe,
  Lock,
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

interface KBArticle {
  id: number;
  title: string;
  content: string;
  category: string;
  tags?: string;
  url?: string;
  is_public: boolean;
  created_by: string;
  created_at: string;
  updated_at: string;
  view_count: number;
}

interface NewArticleData {
  title: string;
  content: string;
  category: string;
  tags?: string;
  url?: string;
  is_public: boolean;
  created_by: string;
}

interface Category {
  category: string;
  count: number;
}

const SUPPORT_API_BASE = 'http://localhost:8510';

export default function KB() {
  const [articles, setArticles] = useState<KBArticle[]>([]);
  const [categories, setCategories] = useState<Category[]>([]);
  const [popularArticles, setPopularArticles] = useState<KBArticle[]>([]);
  const [selectedArticle, setSelectedArticle] = useState<KBArticle | null>(
    null
  );
  const [loading, setLoading] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [categoryFilter, setCategoryFilter] = useState<string>('all');
  const [showNewArticleDialog, setShowNewArticleDialog] = useState(false);
  const [showArticleDialog, setShowArticleDialog] = useState(false);
  const [editMode, setEditMode] = useState(false);
  const [newArticle, setNewArticle] = useState<NewArticleData>({
    title: '',
    content: '',
    category: '',
    tags: '',
    url: '',
    is_public: true,
    created_by: 'admin',
  });

  const fetchArticles = useCallback(async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (categoryFilter !== 'all') params.append('category', categoryFilter);
      if (searchTerm) params.append('search', searchTerm);

      const response = await fetch(`${SUPPORT_API_BASE}/kb?${params}`);
      if (response.ok) {
        const data = await response.json();
        setArticles(data);
      }
    } catch {
      // Handle error silently
    } finally {
      setLoading(false);
    }
  }, [categoryFilter, searchTerm]);

  const fetchCategories = async () => {
    try {
      const response = await fetch(`${SUPPORT_API_BASE}/kb/categories/list`);
      if (response.ok) {
        const data = await response.json();
        setCategories(data);
      }
    } catch {
      // Handle error silently
    }
  };

  const fetchPopularArticles = async () => {
    try {
      const response = await fetch(
        `${SUPPORT_API_BASE}/kb/popular/articles?limit=5`
      );
      if (response.ok) {
        const data = await response.json();
        setPopularArticles(data);
      }
    } catch {
      // Handle error silently
    }
  };

  const createArticle = async () => {
    if (!newArticle.title || !newArticle.content || !newArticle.category)
      return;

    try {
      const response = await fetch(`${SUPPORT_API_BASE}/kb`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(newArticle),
      });

      if (response.ok) {
        setNewArticle({
          title: '',
          content: '',
          category: '',
          tags: '',
          url: '',
          is_public: true,
          created_by: 'admin',
        });
        setShowNewArticleDialog(false);
        fetchArticles();
        fetchCategories();
      }
    } catch {
      // Handle error silently
    }
  };

  const updateArticle = async () => {
    if (!selectedArticle) return;

    try {
      const response = await fetch(
        `${SUPPORT_API_BASE}/kb/${selectedArticle.id}`,
        {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            title: newArticle.title,
            content: newArticle.content,
            category: newArticle.category,
            tags: newArticle.tags,
            url: newArticle.url,
            is_public: newArticle.is_public,
          }),
        }
      );

      if (response.ok) {
        const updatedArticle = await response.json();
        setSelectedArticle(updatedArticle);
        setEditMode(false);
        fetchArticles();
        fetchCategories();
      }
    } catch {
      // Handle error silently
    }
  };

  const deleteArticle = async (articleId: number) => {
    if (!confirm('Are you sure you want to delete this article?')) return;

    try {
      const response = await fetch(`${SUPPORT_API_BASE}/kb/${articleId}`, {
        method: 'DELETE',
      });

      if (response.ok) {
        fetchArticles();
        fetchCategories();
        if (selectedArticle?.id === articleId) {
          setShowArticleDialog(false);
          setSelectedArticle(null);
        }
      }
    } catch {
      // Handle error silently
    }
  };

  const openArticleDialog = async (article: KBArticle) => {
    // Fetch the full article to increment view count
    try {
      const response = await fetch(`${SUPPORT_API_BASE}/kb/${article.id}`);
      if (response.ok) {
        const fullArticle = await response.json();
        setSelectedArticle(fullArticle);
        setShowArticleDialog(true);
      }
    } catch {
      setSelectedArticle(article);
      setShowArticleDialog(true);
    }
  };

  const startEdit = (article: KBArticle) => {
    setNewArticle({
      title: article.title,
      content: article.content,
      category: article.category,
      tags: article.tags || '',
      url: article.url || '',
      is_public: article.is_public,
      created_by: article.created_by,
    });
    setEditMode(true);
  };

  const formatDateTime = (dateString: string) => {
    return new Date(dateString).toLocaleString();
  };

  const parseTagsToArray = (tags?: string) => {
    return tags
      ? tags
          .split(',')
          .map(tag => tag.trim())
          .filter(tag => tag)
      : [];
  };

  useEffect(() => {
    fetchArticles();
    fetchCategories();
    fetchPopularArticles();
  }, [fetchArticles]);

  return (
    <div className='space-y-6'>
      {/* Header */}
      <div className='flex justify-between items-center'>
        <div>
          <h1 className='text-3xl font-bold'>Knowledge Base</h1>
          <p className='text-gray-600'>
            Manage articles, documentation, and helpful resources
          </p>
        </div>
        <div className='flex gap-2'>
          <Button
            onClick={() => {
              fetchArticles();
              fetchCategories();
              fetchPopularArticles();
            }}
            variant='outline'
            size='sm'
          >
            <RefreshCw className='h-4 w-4 mr-2' />
            Refresh
          </Button>
          <Dialog
            open={showNewArticleDialog}
            onOpenChange={setShowNewArticleDialog}
          >
            <DialogTrigger>
              <Button>
                <Plus className='h-4 w-4 mr-2' />
                New Article
              </Button>
            </DialogTrigger>
            <DialogContent className='max-w-2xl'>
              <DialogHeader>
                <DialogTitle>Create New Article</DialogTitle>
              </DialogHeader>
              <div className='space-y-4'>
                <Input
                  placeholder='Article title'
                  value={newArticle.title}
                  onChange={e =>
                    setNewArticle({ ...newArticle, title: e.target.value })
                  }
                />
                <Input
                  placeholder='Category'
                  value={newArticle.category}
                  onChange={e =>
                    setNewArticle({ ...newArticle, category: e.target.value })
                  }
                />
                <Textarea
                  placeholder='Content'
                  value={newArticle.content}
                  onChange={e =>
                    setNewArticle({ ...newArticle, content: e.target.value })
                  }
                  rows={8}
                />
                <Input
                  placeholder='Tags (comma-separated)'
                  value={newArticle.tags}
                  onChange={e =>
                    setNewArticle({ ...newArticle, tags: e.target.value })
                  }
                />
                <Input
                  placeholder='External URL (optional)'
                  value={newArticle.url}
                  onChange={e =>
                    setNewArticle({ ...newArticle, url: e.target.value })
                  }
                />
                <div className='flex items-center gap-2'>
                  <input
                    type='checkbox'
                    checked={newArticle.is_public}
                    onChange={e =>
                      setNewArticle({
                        ...newArticle,
                        is_public: e.target.checked,
                      })
                    }
                    id='public-checkbox'
                  />
                  <label htmlFor='public-checkbox' className='text-sm'>
                    Make article public
                  </label>
                </div>
                <Button onClick={createArticle} className='w-full'>
                  Create Article
                </Button>
              </div>
            </DialogContent>
          </Dialog>
        </div>
      </div>

      {/* Stats */}
      <div className='grid grid-cols-1 md:grid-cols-3 gap-4'>
        <div className='bg-white p-6 rounded-lg border shadow-sm'>
          <div className='flex items-center justify-between'>
            <div>
              <p className='text-sm text-gray-600'>Total Articles</p>
              <p className='text-2xl font-bold'>{articles.length}</p>
            </div>
            <BookOpen className='h-8 w-8 text-blue-500' />
          </div>
        </div>
        <div className='bg-white p-6 rounded-lg border shadow-sm'>
          <div className='flex items-center justify-between'>
            <div>
              <p className='text-sm text-gray-600'>Categories</p>
              <p className='text-2xl font-bold'>{categories.length}</p>
            </div>
            <Tag className='h-8 w-8 text-green-500' />
          </div>
        </div>
        <div className='bg-white p-6 rounded-lg border shadow-sm'>
          <div className='flex items-center justify-between'>
            <div>
              <p className='text-sm text-gray-600'>Total Views</p>
              <p className='text-2xl font-bold'>
                {articles.reduce((sum, article) => sum + article.view_count, 0)}
              </p>
            </div>
            <Eye className='h-8 w-8 text-purple-500' />
          </div>
        </div>
      </div>

      {/* Popular Articles */}
      {popularArticles.length > 0 && (
        <div className='bg-white p-6 rounded-lg border shadow-sm'>
          <h2 className='text-lg font-semibold mb-4'>Popular Articles</h2>
          <div className='space-y-2'>
            {popularArticles.map(article => (
              <div
                key={article.id}
                className='flex items-center justify-between p-3 rounded-lg bg-gray-50 hover:bg-gray-100 cursor-pointer'
                onClick={() => openArticleDialog(article)}
              >
                <div className='flex items-center gap-3'>
                  <BookOpen className='h-5 w-5 text-gray-400' />
                  <div>
                    <p className='font-medium'>{article.title}</p>
                    <p className='text-sm text-gray-600'>{article.category}</p>
                  </div>
                </div>
                <div className='flex items-center gap-2'>
                  <Badge variant='secondary'>{article.view_count} views</Badge>
                  {article.url && (
                    <ExternalLink className='h-4 w-4 text-gray-400' />
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Filters */}
      <div className='bg-white p-4 rounded-lg border shadow-sm'>
        <div className='flex flex-wrap gap-4'>
          <div className='flex items-center gap-2'>
            <Search className='h-4 w-4 text-gray-500' />
            <Input
              placeholder='Search articles...'
              value={searchTerm}
              onChange={e => setSearchTerm(e.target.value)}
              className='w-64'
            />
          </div>
          <Select value={categoryFilter} onValueChange={setCategoryFilter}>
            <SelectTrigger className='w-48'>
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value='all'>All Categories</SelectItem>
              {categories.map(category => (
                <SelectItem key={category.category} value={category.category}>
                  {category.category} ({category.count})
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      </div>

      {/* Articles Table */}
      <div className='bg-white rounded-lg border shadow-sm'>
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Title</TableHead>
              <TableHead>Category</TableHead>
              <TableHead>Tags</TableHead>
              <TableHead>Visibility</TableHead>
              <TableHead>Views</TableHead>
              <TableHead>Created</TableHead>
              <TableHead>Actions</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {loading ? (
              <TableRow>
                <TableCell colSpan={7} className='text-center py-8'>
                  Loading articles...
                </TableCell>
              </TableRow>
            ) : articles.length === 0 ? (
              <TableRow>
                <TableCell
                  colSpan={7}
                  className='text-center py-8 text-gray-500'
                >
                  No articles found
                </TableCell>
              </TableRow>
            ) : (
              articles.map(article => (
                <TableRow
                  key={article.id}
                  className='cursor-pointer hover:bg-gray-50'
                  onClick={() => openArticleDialog(article)}
                >
                  <TableCell className='font-medium max-w-xs'>
                    <div className='flex items-center gap-2'>
                      <span className='truncate'>{article.title}</span>
                      {article.url && (
                        <ExternalLink className='h-4 w-4 text-gray-400' />
                      )}
                    </div>
                  </TableCell>
                  <TableCell>
                    <Badge variant='outline'>{article.category}</Badge>
                  </TableCell>
                  <TableCell>
                    <div className='flex flex-wrap gap-1'>
                      {parseTagsToArray(article.tags)
                        .slice(0, 3)
                        .map((tag, index) => (
                          <Badge
                            key={index}
                            variant='secondary'
                            className='text-xs'
                          >
                            {tag}
                          </Badge>
                        ))}
                      {parseTagsToArray(article.tags).length > 3 && (
                        <Badge variant='secondary' className='text-xs'>
                          +{parseTagsToArray(article.tags).length - 3}
                        </Badge>
                      )}
                    </div>
                  </TableCell>
                  <TableCell>
                    <div className='flex items-center gap-1'>
                      {article.is_public ? (
                        <Globe className='h-4 w-4 text-green-500' />
                      ) : (
                        <Lock className='h-4 w-4 text-gray-500' />
                      )}
                      <span className='text-sm'>
                        {article.is_public ? 'Public' : 'Private'}
                      </span>
                    </div>
                  </TableCell>
                  <TableCell>{article.view_count}</TableCell>
                  <TableCell>{formatDateTime(article.created_at)}</TableCell>
                  <TableCell>
                    <div className='flex gap-1'>
                      <Button
                        size='sm'
                        variant='outline'
                        onClick={e => {
                          e.stopPropagation();
                          startEdit(article);
                          setSelectedArticle(article);
                          setShowArticleDialog(true);
                        }}
                      >
                        <Edit className='h-4 w-4' />
                      </Button>
                      <Button
                        size='sm'
                        variant='outline'
                        onClick={e => {
                          e.stopPropagation();
                          deleteArticle(article.id);
                        }}
                      >
                        <Trash2 className='h-4 w-4' />
                      </Button>
                    </div>
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </div>

      {/* Article Detail Dialog */}
      <Dialog
        open={showArticleDialog}
        onOpenChange={open => {
          setShowArticleDialog(open);
          if (!open) {
            setEditMode(false);
            setSelectedArticle(null);
          }
        }}
      >
        <DialogContent className='max-w-4xl max-h-[90vh] overflow-y-auto'>
          {selectedArticle && (
            <>
              <DialogHeader>
                <DialogTitle className='flex items-center justify-between'>
                  <span>
                    {editMode ? 'Edit Article' : selectedArticle.title}
                  </span>
                  <div className='flex items-center gap-2'>
                    {!editMode && (
                      <>
                        <Button
                          size='sm'
                          variant='outline'
                          onClick={() => startEdit(selectedArticle)}
                        >
                          <Edit className='h-4 w-4 mr-2' />
                          Edit
                        </Button>
                        <Button
                          size='sm'
                          variant='outline'
                          onClick={() => deleteArticle(selectedArticle.id)}
                        >
                          <Trash2 className='h-4 w-4 mr-2' />
                          Delete
                        </Button>
                      </>
                    )}
                  </div>
                </DialogTitle>
              </DialogHeader>

              <div className='space-y-6'>
                {editMode ? (
                  /* Edit Mode */
                  <div className='space-y-4'>
                    <Input
                      placeholder='Article title'
                      value={newArticle.title}
                      onChange={e =>
                        setNewArticle({ ...newArticle, title: e.target.value })
                      }
                    />
                    <Input
                      placeholder='Category'
                      value={newArticle.category}
                      onChange={e =>
                        setNewArticle({
                          ...newArticle,
                          category: e.target.value,
                        })
                      }
                    />
                    <Textarea
                      placeholder='Content'
                      value={newArticle.content}
                      onChange={e =>
                        setNewArticle({
                          ...newArticle,
                          content: e.target.value,
                        })
                      }
                      rows={12}
                    />
                    <Input
                      placeholder='Tags (comma-separated)'
                      value={newArticle.tags}
                      onChange={e =>
                        setNewArticle({ ...newArticle, tags: e.target.value })
                      }
                    />
                    <Input
                      placeholder='External URL (optional)'
                      value={newArticle.url}
                      onChange={e =>
                        setNewArticle({ ...newArticle, url: e.target.value })
                      }
                    />
                    <div className='flex items-center gap-2'>
                      <input
                        type='checkbox'
                        checked={newArticle.is_public}
                        onChange={e =>
                          setNewArticle({
                            ...newArticle,
                            is_public: e.target.checked,
                          })
                        }
                        id='edit-public-checkbox'
                      />
                      <label htmlFor='edit-public-checkbox' className='text-sm'>
                        Make article public
                      </label>
                    </div>
                    <div className='flex gap-2'>
                      <Button onClick={updateArticle}>Save Changes</Button>
                      <Button
                        variant='outline'
                        onClick={() => setEditMode(false)}
                      >
                        Cancel
                      </Button>
                    </div>
                  </div>
                ) : (
                  /* View Mode */
                  <>
                    {/* Article Info */}
                    <div className='grid grid-cols-2 gap-4 p-4 bg-gray-50 rounded-lg'>
                      <div>
                        <p className='text-sm text-gray-600'>Category</p>
                        <Badge variant='outline'>
                          {selectedArticle.category}
                        </Badge>
                      </div>
                      <div>
                        <p className='text-sm text-gray-600'>Visibility</p>
                        <div className='flex items-center gap-1'>
                          {selectedArticle.is_public ? (
                            <Globe className='h-4 w-4 text-green-500' />
                          ) : (
                            <Lock className='h-4 w-4 text-gray-500' />
                          )}
                          <span className='text-sm'>
                            {selectedArticle.is_public ? 'Public' : 'Private'}
                          </span>
                        </div>
                      </div>
                      <div>
                        <p className='text-sm text-gray-600'>Created by</p>
                        <p className='font-medium'>
                          {selectedArticle.created_by}
                        </p>
                      </div>
                      <div>
                        <p className='text-sm text-gray-600'>Views</p>
                        <p className='font-medium'>
                          {selectedArticle.view_count}
                        </p>
                      </div>
                      <div>
                        <p className='text-sm text-gray-600'>Created</p>
                        <p className='font-medium'>
                          {formatDateTime(selectedArticle.created_at)}
                        </p>
                      </div>
                      <div>
                        <p className='text-sm text-gray-600'>Last updated</p>
                        <p className='font-medium'>
                          {formatDateTime(selectedArticle.updated_at)}
                        </p>
                      </div>
                    </div>

                    {/* Tags */}
                    {selectedArticle.tags && (
                      <div>
                        <h3 className='text-lg font-semibold mb-2'>Tags</h3>
                        <div className='flex flex-wrap gap-2'>
                          {parseTagsToArray(selectedArticle.tags).map(
                            (tag, index) => (
                              <Badge key={index} variant='secondary'>
                                {tag}
                              </Badge>
                            )
                          )}
                        </div>
                      </div>
                    )}

                    {/* External URL */}
                    {selectedArticle.url && (
                      <div>
                        <h3 className='text-lg font-semibold mb-2'>
                          External Link
                        </h3>
                        <a
                          href={selectedArticle.url}
                          target='_blank'
                          rel='noopener noreferrer'
                          className='inline-flex items-center gap-2 text-blue-600 hover:text-blue-800'
                        >
                          <ExternalLink className='h-4 w-4' />
                          {selectedArticle.url}
                        </a>
                      </div>
                    )}

                    {/* Content */}
                    <div>
                      <h3 className='text-lg font-semibold mb-2'>Content</h3>
                      <div className='prose max-w-none'>
                        <div className='whitespace-pre-wrap text-gray-700 bg-gray-50 p-4 rounded-lg'>
                          {selectedArticle.content}
                        </div>
                      </div>
                    </div>
                  </>
                )}
              </div>
            </>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}

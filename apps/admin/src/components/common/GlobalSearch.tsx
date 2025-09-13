import {
  Search,
  User,
  Monitor,
  CreditCard,
  FileText,
  Shield,
  Receipt,
  Clock,
  ExternalLink,
  Bookmark,
  Share,
  Filter,
  X,
  Loader2,
} from 'lucide-react';
import React, { useState, useEffect, useCallback, useRef } from 'react';
import { useNavigate } from 'react-router-dom';

import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Separator } from '@/components/ui/separator';
import { useDebounce } from '@/hooks/useDebounce';

// Types
interface SearchHit {
  id: string;
  type: string;
  title: string;
  content: string;
  score: number;
  metadata: Record<string, unknown>;
  highlighted: Record<string, string[]>;
}

interface SearchResponse {
  hits: SearchHit[];
  total: number;
  took: number;
  aggregations: Record<string, unknown>;
}

interface SavedView {
  id: string;
  name: string;
  query: string;
  filters: Record<string, unknown>;
  created_at: string;
  shared: boolean;
  url?: string;
}

// Entity type configuration
const ENTITY_TYPES = {
  user: {
    icon: User,
    label: 'Users',
    color: 'bg-blue-100 text-blue-800',
    route: '/users',
  },
  device: {
    icon: Monitor,
    label: 'Devices',
    color: 'bg-green-100 text-green-800',
    route: '/devices',
  },
  subscription: {
    icon: CreditCard,
    label: 'Subscriptions',
    color: 'bg-purple-100 text-purple-800',
    route: '/subscriptions',
  },
  invoice: {
    icon: Receipt,
    label: 'Invoices',
    color: 'bg-yellow-100 text-yellow-800',
    route: '/billing/invoices',
  },
  report: {
    icon: FileText,
    label: 'Reports',
    color: 'bg-indigo-100 text-indigo-800',
    route: '/reports',
  },
  audit_log: {
    icon: Shield,
    label: 'Audit Logs',
    color: 'bg-red-100 text-red-800',
    route: '/security/audit-logs',
  },
};

interface GlobalSearchProps {
  isOpen: boolean;
  onClose: () => void;
}

const GlobalSearch: React.FC<GlobalSearchProps> = ({ isOpen, onClose }) => {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<SearchHit[]>([]);
  const [loading, setLoading] = useState(false);
  const [selectedIndex, setSelectedIndex] = useState(0);
  const [recentSearches, setRecentSearches] = useState<string[]>([]);
  const [savedViews, setSavedViews] = useState<SavedView[]>([]);
  const [showSavedViews, setShowSavedViews] = useState(false);
  const [filters, setFilters] = useState<Record<string, unknown>>({});

  const navigate = useNavigate();
  const inputRef = useRef<HTMLInputElement>(null);
  const debouncedQuery = useDebounce(query, 300);

  // Load saved data from localStorage
  useEffect(() => {
    const saved = localStorage.getItem('admin-recent-searches');
    if (saved) {
      try {
        setRecentSearches(JSON.parse(saved).slice(0, 5));
      } catch {
        // Handle parse error silently
      }
    }

    const savedViewsData = localStorage.getItem('admin-saved-views');
    if (savedViewsData) {
      try {
        setSavedViews(JSON.parse(savedViewsData));
      } catch {
        // Handle parse error silently
      }
    }
  }, []);

  // Focus input when dialog opens
  useEffect(() => {
    if (isOpen && inputRef.current) {
      setTimeout(() => inputRef.current?.focus(), 100);
    }
  }, [isOpen]);

  const handleResultClick = useCallback(
    (hit: SearchHit) => {
      const entityConfig = ENTITY_TYPES[hit.type as keyof typeof ENTITY_TYPES];
      if (entityConfig) {
        const route = `${entityConfig.route}/${hit.id}`;
        navigate(route);
        onClose();
      }
    },
    [navigate, onClose]
  );

  // Perform search
  const performSearch = useCallback(
    async (searchQuery: string) => {
      if (!searchQuery.trim()) {
        setResults([]);
        return;
      }

      setLoading(true);
      try {
        // Build query parameters
        const params = new URLSearchParams({
          q: searchQuery,
          scope: 'admin_all',
          size: '20',
          user_id: 'current-user', // Would come from auth context
          role: 'system_admin', // Would come from auth context
        });

        // Add filters if any
        if (Object.keys(filters).length > 0) {
          params.append('filters', JSON.stringify(filters));
        }

        const response = await fetch(`/api/search?${params}`);
        const data: SearchResponse = await response.json();

        setResults(data.hits || []);
        setSelectedIndex(0);

        // Save to recent searches
        const newRecent = [
          searchQuery,
          ...recentSearches.filter(q => q !== searchQuery),
        ].slice(0, 5);
        setRecentSearches(newRecent);
        localStorage.setItem(
          'admin-recent-searches',
          JSON.stringify(newRecent)
        );
      } catch (error) {
        // Log error in development only
        if (process.env.NODE_ENV === 'development') {
          console.error('Search failed:', error);
        }
        setResults([]);
      } finally {
        setLoading(false);
      }
    },
    [filters, recentSearches]
  );

  // Debounced search effect
  useEffect(() => {
    if (debouncedQuery) {
      performSearch(debouncedQuery);
    } else {
      setResults([]);
    }
  }, [debouncedQuery, performSearch]);

  // Keyboard navigation
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (!isOpen) return;

      switch (e.key) {
        case 'ArrowDown':
          e.preventDefault();
          setSelectedIndex(prev => Math.min(prev + 1, results.length - 1));
          break;
        case 'ArrowUp':
          e.preventDefault();
          setSelectedIndex(prev => Math.max(prev - 1, 0));
          break;
        case 'Enter':
          e.preventDefault();
          if (results[selectedIndex]) {
            handleResultClick(results[selectedIndex]);
          }
          break;
        case 'Escape':
          onClose();
          break;
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, results, selectedIndex, handleResultClick, onClose]);

  const handleRecentSearchClick = (recentQuery: string) => {
    setQuery(recentQuery);
    performSearch(recentQuery);
  };

  const saveCurrentView = () => {
    if (!query.trim()) return;

    const newView: SavedView = {
      id: `view-${Date.now()}`,
      name: query.slice(0, 50),
      query,
      filters,
      created_at: new Date().toISOString(),
      shared: false,
    };

    const updated = [...savedViews, newView];
    setSavedViews(updated);
    localStorage.setItem('admin-saved-views', JSON.stringify(updated));
  };

  const shareView = (view: SavedView) => {
    const params = new URLSearchParams({
      q: view.query,
      filters: JSON.stringify(view.filters),
    });
    const shareUrl = `${window.location.origin}/admin/search?${params}`;

    navigator.clipboard.writeText(shareUrl).catch(() => {
      // Handle clipboard error silently
    });

    // Update view with share URL
    const updated = savedViews.map(v =>
      v.id === view.id ? { ...v, shared: true, url: shareUrl } : v
    );
    setSavedViews(updated);
    localStorage.setItem('admin-saved-views', JSON.stringify(updated));
  };

  const deleteSavedView = (viewId: string) => {
    const updated = savedViews.filter(v => v.id !== viewId);
    setSavedViews(updated);
    localStorage.setItem('admin-saved-views', JSON.stringify(updated));
  };

  const clearFilters = () => {
    setFilters({});
  };

  const addTypeFilter = (type: string) => {
    setFilters(prev => ({
      ...prev,
      type: [...(Array.isArray(prev.type) ? prev.type : []), type],
    }));
  };

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className='max-w-2xl max-h-[80vh] p-0'>
        <DialogHeader className='px-6 py-4 border-b'>
          <DialogTitle className='flex items-center gap-2'>
            <Search className='h-5 w-5' />
            Global Search
          </DialogTitle>
        </DialogHeader>

        <div className='p-6 space-y-4'>
          {/* Search Input */}
          <div className='relative'>
            <Search className='absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400' />
            <Input
              ref={inputRef}
              placeholder='Search users, devices, subscriptions, invoices, reports, audit logs...'
              value={query}
              onChange={e => setQuery(e.target.value)}
              className='pl-10 pr-10'
            />
            {loading && (
              <Loader2 className='absolute right-3 top-1/2 transform -translate-y-1/2 h-4 w-4 animate-spin text-gray-400' />
            )}
          </div>

          {/* Filters */}
          {Object.keys(filters).length > 0 && (
            <div className='flex items-center gap-2 flex-wrap'>
              <span className='text-sm text-gray-500'>Filters:</span>
              {Object.entries(filters).map(([key, value]) => (
                <Badge key={key} variant='secondary' className='gap-1'>
                  {key}:{' '}
                  {Array.isArray(value) ? value.join(', ') : String(value)}
                  <X
                    className='h-3 w-3 cursor-pointer'
                    onClick={() =>
                      setFilters(prev => ({ ...prev, [key]: undefined }))
                    }
                  />
                </Badge>
              ))}
              <Button variant='ghost' size='sm' onClick={clearFilters}>
                Clear all
              </Button>
            </div>
          )}

          {/* Action Buttons */}
          <div className='flex items-center gap-2'>
            <Button
              variant='outline'
              size='sm'
              onClick={() => setShowSavedViews(!showSavedViews)}
            >
              <Bookmark className='h-4 w-4 mr-1' />
              Saved Views ({savedViews.length})
            </Button>
            {query && (
              <Button variant='outline' size='sm' onClick={saveCurrentView}>
                <Bookmark className='h-4 w-4 mr-1' />
                Save View
              </Button>
            )}
            <Button variant='outline' size='sm'>
              <Filter className='h-4 w-4 mr-1' />
              Filters
            </Button>
          </div>

          <Separator />

          {/* Results or Initial State */}
          <ScrollArea className='h-96'>
            {query && results.length > 0 ? (
              <div className='space-y-2'>
                {results.map((hit, index) => {
                  const entityConfig =
                    ENTITY_TYPES[hit.type as keyof typeof ENTITY_TYPES];
                  const Icon = entityConfig?.icon || FileText;

                  return (
                    <div
                      key={hit.id}
                      className={`p-3 rounded-lg border cursor-pointer transition-colors ${
                        index === selectedIndex
                          ? 'bg-blue-50 border-blue-200'
                          : 'hover:bg-gray-50'
                      }`}
                      onClick={() => handleResultClick(hit)}
                    >
                      <div className='flex items-start gap-3'>
                        <Icon className='h-5 w-5 mt-0.5 text-gray-500' />
                        <div className='flex-1 min-w-0'>
                          <div className='flex items-center gap-2'>
                            <h3 className='font-medium text-sm truncate'>
                              {hit.title}
                            </h3>
                            <Badge
                              className={`text-xs ${entityConfig?.color || 'bg-gray-100 text-gray-800'}`}
                            >
                              {entityConfig?.label || hit.type}
                            </Badge>
                          </div>
                          <p className='text-sm text-gray-600 mt-1 line-clamp-2'>
                            {hit.content || 'No description available'}
                          </p>
                          {hit.metadata.updated_at &&
                            typeof hit.metadata.updated_at === 'string' && (
                              <div className='flex items-center gap-1 mt-2 text-xs text-gray-400'>
                                <Clock className='h-3 w-3' />
                                <span>
                                  Updated{' '}
                                  {new Date(
                                    hit.metadata.updated_at
                                  ).toLocaleDateString()}
                                </span>
                              </div>
                            )}
                        </div>
                        <ExternalLink className='h-4 w-4 text-gray-400' />
                      </div>
                    </div>
                  );
                })}
              </div>
            ) : query && !loading ? (
              <div className='text-center py-8 text-gray-500'>
                <Search className='h-8 w-8 mx-auto mb-2 opacity-50' />
                <p>No results found for "{query}"</p>
                <p className='text-sm mt-1'>
                  Try adjusting your search terms or filters
                </p>
              </div>
            ) : !query ? (
              <div className='space-y-4'>
                {/* Recent Searches */}
                {recentSearches.length > 0 && (
                  <div>
                    <h3 className='font-medium text-sm mb-2'>
                      Recent Searches
                    </h3>
                    <div className='space-y-1'>
                      {recentSearches.map((recent, index) => (
                        <div
                          key={index}
                          className='p-2 rounded hover:bg-gray-50 cursor-pointer text-sm'
                          onClick={() => handleRecentSearchClick(recent)}
                        >
                          <div className='flex items-center gap-2'>
                            <Clock className='h-4 w-4 text-gray-400' />
                            {recent}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Entity Type Quick Filters */}
                <div>
                  <h3 className='font-medium text-sm mb-2'>Search by Type</h3>
                  <div className='grid grid-cols-2 gap-2'>
                    {Object.entries(ENTITY_TYPES).map(([type, config]) => {
                      const Icon = config.icon;
                      return (
                        <div
                          key={type}
                          className='p-2 rounded border hover:bg-gray-50 cursor-pointer text-sm'
                          onClick={() => addTypeFilter(type)}
                        >
                          <div className='flex items-center gap-2'>
                            <Icon className='h-4 w-4 text-gray-500' />
                            {config.label}
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>

                {/* Saved Views */}
                {showSavedViews && savedViews.length > 0 && (
                  <div>
                    <h3 className='font-medium text-sm mb-2'>Saved Views</h3>
                    <div className='space-y-2'>
                      {savedViews.map(view => (
                        <div key={view.id} className='p-2 rounded border'>
                          <div className='flex items-center justify-between'>
                            <div
                              className='flex-1 cursor-pointer'
                              onClick={() => {
                                setQuery(view.query);
                                setFilters(view.filters);
                              }}
                            >
                              <p className='font-medium text-sm'>{view.name}</p>
                              <p className='text-xs text-gray-500'>
                                Created{' '}
                                {new Date(view.created_at).toLocaleDateString()}
                              </p>
                            </div>
                            <div className='flex items-center gap-1'>
                              <Button
                                variant='ghost'
                                size='sm'
                                onClick={() => shareView(view)}
                              >
                                <Share className='h-3 w-3' />
                              </Button>
                              <Button
                                variant='ghost'
                                size='sm'
                                onClick={() => deleteSavedView(view.id)}
                              >
                                <X className='h-3 w-3' />
                              </Button>
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            ) : null}
          </ScrollArea>
        </div>

        {/* Footer */}
        <div className='px-6 py-3 border-t bg-gray-50 text-xs text-gray-500'>
          <div className='flex items-center justify-between'>
            <span>Press ↑↓ to navigate, Enter to select, Esc to close</span>
            <span>{results.length > 0 && `${results.length} results`}</span>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
};

export default GlobalSearch;

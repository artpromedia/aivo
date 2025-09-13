import React, { useEffect, useState } from 'react';
import { useSearchParams } from 'react-router-dom';

import GlobalSearch from '@/components/common/GlobalSearch';

const SearchPage: React.FC = () => {
  const [searchParams] = useSearchParams();
  const [isSearchOpen, setIsSearchOpen] = useState(true);

  useEffect(() => {
    // If the page loads with search parameters, open the search modal
    const query = searchParams.get('q');
    if (query) {
      setIsSearchOpen(true);
    }
  }, [searchParams]);

  return (
    <div className='p-6'>
      <div className='max-w-4xl mx-auto'>
        <h1 className='text-2xl font-bold mb-6'>Search Results</h1>

        <div className='text-center py-12'>
          <p className='text-gray-600 mb-4'>
            Use the search dialog to find users, devices, subscriptions, and
            more.
          </p>
          <button
            onClick={() => setIsSearchOpen(true)}
            className='px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700'
          >
            Open Search
          </button>
        </div>
      </div>

      <GlobalSearch
        isOpen={isSearchOpen}
        onClose={() => setIsSearchOpen(false)}
      />
    </div>
  );
};

export default SearchPage;

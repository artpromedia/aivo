import React, { useState, useEffect, useCallback } from 'react';

// Types
interface Banner {
  id: string;
  message: string;
  type: 'info' | 'warning' | 'critical';
  target_audience: 'all' | 'admins' | 'tenants';
}

// Styles based on banner type
const getBannerStyles = (type: string) => {
  const baseStyles = {
    padding: '12px 16px',
    margin: '0 0 16px 0',
    borderRadius: '4px',
    fontWeight: 'bold' as const,
    textAlign: 'center' as const,
    position: 'relative' as const,
    fontSize: '14px',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
  };

  switch (type) {
    case 'info':
      return {
        ...baseStyles,
        backgroundColor: '#e3f2fd',
        color: '#1976d2',
        border: '1px solid #2196f3',
      };
    case 'warning':
      return {
        ...baseStyles,
        backgroundColor: '#fff3e0',
        color: '#ef6c00',
        border: '1px solid #ff9800',
      };
    case 'critical':
      return {
        ...baseStyles,
        backgroundColor: '#ffebee',
        color: '#c62828',
        border: '1px solid #f44336',
      };
    default:
      return {
        ...baseStyles,
        backgroundColor: '#f5f5f5',
        color: '#666',
        border: '1px solid #ddd',
      };
  }
};

const closeButtonStyles = {
  background: 'none',
  border: 'none',
  fontSize: '18px',
  cursor: 'pointer',
  padding: '0',
  marginLeft: '16px',
  opacity: 0.7,
};

// API service
class BannerService {
  private baseUrl = '/api/v1/banners';

  async getActiveBanners(audience = 'admins') {
    try {
      const response = await fetch(
        `${this.baseUrl}/active?target_audience=${audience}`
      );
      if (!response.ok) {
        throw new Error('Failed to fetch banners');
      }
      return response.json();
    } catch {
      // Silently handle error - banners are not critical
      return { banners: [] };
    }
  }
}

const bannerService = new BannerService();

// Main component
interface BannerDisplayProps {
  audience?: 'all' | 'admins' | 'tenants';
  onBannerDismiss?: (bannerId: string) => void;
}

const BannerDisplay: React.FC<BannerDisplayProps> = ({
  audience = 'admins',
  onBannerDismiss,
}) => {
  const [banners, setBanners] = useState<Banner[]>([]);
  const [dismissedBanners, setDismissedBanners] = useState<Set<string>>(
    new Set()
  );
  const [loading, setLoading] = useState(true);

  const loadBanners = useCallback(async () => {
    try {
      const response = await bannerService.getActiveBanners(audience);
      setBanners(response.banners || []);
    } catch {
      // Silently handle error - banners are not critical
    } finally {
      setLoading(false);
    }
  }, [audience]);

  useEffect(() => {
    loadBanners();

    // Set up periodic refresh every 30 seconds
    const interval = setInterval(loadBanners, 30000);

    return () => clearInterval(interval);
  }, [loadBanners]);

  const handleDismiss = (bannerId: string) => {
    setDismissedBanners(prev => new Set([...prev, bannerId]));

    if (onBannerDismiss) {
      onBannerDismiss(bannerId);
    }
  };

  // Filter out dismissed banners and those not for this audience
  const visibleBanners = banners.filter(
    banner =>
      !dismissedBanners.has(banner.id) &&
      (banner.target_audience === audience || banner.target_audience === 'all')
  );

  if (loading || visibleBanners.length === 0) {
    return null;
  }

  return (
    <div style={{ width: '100%' }}>
      {visibleBanners.map(banner => (
        <div key={banner.id} style={getBannerStyles(banner.type)}>
          <span style={{ flex: 1 }}>{banner.message}</span>
          <button
            onClick={() => handleDismiss(banner.id)}
            style={{
              ...closeButtonStyles,
              color: getBannerStyles(banner.type).color,
            }}
            title='Dismiss banner'
          >
            ×
          </button>
        </div>
      ))}
    </div>
  );
};

export default BannerDisplay;

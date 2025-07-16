import React from 'react';
import { ArrowUpIcon, ArrowDownIcon } from '@heroicons/react/24/outline';
import clsx from 'clsx';

interface StatsCardProps {
  title: string;
  value: string | number;
  change?: number;
  changeType?: 'positive' | 'negative' | 'neutral';
  icon?: React.ComponentType<{ className?: string }>;
  description?: string;
}

const StatsCard: React.FC<StatsCardProps> = ({
  title,
  value,
  change,
  changeType = 'neutral',
  icon: Icon,
  description,
}) => {
  const formatChange = (change: number) => {
    const sign = change > 0 ? '+' : '';
    return `${sign}${change.toFixed(1)}%`;
  };

  const getChangeColor = (type: string) => {
    switch (type) {
      case 'positive':
        return 'text-success-600';
      case 'negative':
        return 'text-error-600';
      default:
        return 'text-secondary-600';
    }
  };

  const getChangeIcon = (type: string) => {
    switch (type) {
      case 'positive':
        return ArrowUpIcon;
      case 'negative':
        return ArrowDownIcon;
      default:
        return null;
    }
  };

  const ChangeIcon = getChangeIcon(changeType);

  return (
    <div className="bg-white rounded-lg shadow-elevation-1 p-6 border border-secondary-200">
      <div className="flex items-center justify-between">
        <div className="flex-1">
          <p className="text-sm font-medium text-secondary-600">{title}</p>
          <p className="text-2xl font-bold text-secondary-900 mt-1">{value}</p>
          
          {change !== undefined && (
            <div className="flex items-center mt-2">
              {ChangeIcon && (
                <ChangeIcon className={clsx('h-4 w-4 mr-1', getChangeColor(changeType))} />
              )}
              <span className={clsx('text-sm font-medium', getChangeColor(changeType))}>
                {formatChange(change)}
              </span>
              {description && (
                <span className="text-sm text-secondary-500 ml-2">
                  {description}
                </span>
              )}
            </div>
          )}
        </div>
        
        {Icon && (
          <div className="flex-shrink-0">
            <Icon className="h-8 w-8 text-primary-500" />
          </div>
        )}
      </div>
    </div>
  );
};

export default StatsCard;
import React from 'react';
import { useRouter } from 'next/router';
import Link from 'next/link';
import { 
  HomeIcon, 
  ChartBarIcon, 
  BellIcon, 
  Cog6ToothIcon,
  BuildingOfficeIcon,
  MagnifyingGlassIcon,
  DocumentTextIcon,
  ChatBubbleLeftRightIcon,
  GlobeAltIcon,
  UserGroupIcon,
  CurrencyDollarIcon,
  SparklesIcon
} from '@heroicons/react/24/outline';
import { useAuth } from '@/hooks/useAuth';
import clsx from 'clsx';

const navigation = [
  { name: 'Dashboard', href: '/dashboard', icon: HomeIcon },
  { name: 'Monitoring', href: '/monitoring', icon: MagnifyingGlassIcon },
  { name: 'Citations', href: '/citations', icon: DocumentTextIcon },
  { name: 'Analytics', href: '/analytics', icon: ChartBarIcon },
  { name: 'Brands', href: '/brands', icon: BuildingOfficeIcon },
  { name: 'AI Platforms', href: '/platforms', icon: SparklesIcon, badge: 'New' },
  { name: 'Reddit', href: '/reddit', icon: ChatBubbleLeftRightIcon },
  { name: 'Review Sites', href: '/review-sites', icon: GlobeAltIcon },
  { name: 'Competitors', href: '/competitors', icon: UserGroupIcon },
  { name: 'ROI Tracking', href: '/roi', icon: CurrencyDollarIcon },
  { name: 'Alerts', href: '/alerts', icon: BellIcon },
  { name: 'Settings', href: '/settings', icon: Cog6ToothIcon },
];

const Sidebar = () => {
  const router = useRouter();
  const { user, logout } = useAuth();

  return (
    <div className="flex h-screen w-64 flex-col bg-secondary-900">
      {/* Logo */}
      <div className="flex h-16 items-center justify-center border-b border-secondary-800">
        <Link href="/dashboard">
          <div className="flex items-center space-x-2">
            <div className="h-8 w-8 rounded-lg bg-primary-500 flex items-center justify-center">
              <SparklesIcon className="h-5 w-5 text-white" />
            </div>
            <span className="text-xl font-bold text-white">ChatSEO</span>
          </div>
        </Link>
      </div>

      {/* Navigation */}
      <nav className="flex-1 overflow-y-auto px-3 py-4">
        <ul className="space-y-1">
          {navigation.map((item) => {
            const isActive = router.pathname === item.href;
            return (
              <li key={item.name}>
                <Link
                  href={item.href}
                  className={clsx(
                    'group flex items-center px-3 py-2 text-sm font-medium rounded-md transition-colors duration-150',
                    isActive
                      ? 'bg-primary-600 text-white'
                      : 'text-secondary-300 hover:bg-secondary-800 hover:text-white'
                  )}
                >
                  <item.icon
                    className={clsx(
                      'mr-3 h-5 w-5',
                      isActive ? 'text-white' : 'text-secondary-400 group-hover:text-white'
                    )}
                  />
                  {item.name}
                  {item.badge && (
                    <span className="ml-auto rounded-full bg-primary-500 px-2 py-0.5 text-xs font-medium text-white">
                      {item.badge}
                    </span>
                  )}
                </Link>
              </li>
            );
          })}
        </ul>
      </nav>

      {/* User section */}
      <div className="border-t border-secondary-800 p-4">
        <div className="flex items-center">
          <div className="h-8 w-8 rounded-full bg-primary-500 flex items-center justify-center">
            <span className="text-sm font-medium text-white">
              {user?.email?.charAt(0).toUpperCase()}
            </span>
          </div>
          <div className="ml-3 flex-1">
            <p className="text-sm font-medium text-white">{user?.email}</p>
            <p className="text-xs text-secondary-400 capitalize">{user?.plan_type} Plan</p>
          </div>
        </div>
        <button
          onClick={logout}
          className="mt-3 w-full rounded-md bg-secondary-800 px-3 py-2 text-sm font-medium text-secondary-300 hover:bg-secondary-700 hover:text-white transition-colors"
        >
          Sign out
        </button>
      </div>
    </div>
  );
};

export default Sidebar;
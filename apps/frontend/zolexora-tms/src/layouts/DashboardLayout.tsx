import React from 'react';
import { NavLink, Outlet, useNavigate } from 'react-router-dom';
import {
  Truck,
  LayoutDashboard,
  CalendarCheck,
  ClipboardList,
  Radio,
  Users,
  Building2,
  FileText,
  CreditCard,
  Receipt,
  Settings,
  LogOut,
  Shield,
  Crown,
  ChevronRight,
} from 'lucide-react';
import { useAuth } from '../features/auth/useAuth';
import { useApplicationRuntime } from '../providers/ApplicationRuntimeProvider';

interface NavItem {
  name: string;
  href: string;
  icon: React.ElementType;
  badge?: string;
}


/**
 * Module Icon Mapping
 *
 * Maps string icon names to Lucide icon components.
 * Icon names match backend CATEGORY_DEFAULTS in config/constants.py.
 */

import {
  // Navigation & Browser
  Navigation, Globe, Monitor, MousePointerClick, MousePointer, Keyboard,

  // Time & Scheduling
  Clock, Timer, Calendar,

  // Files & Data
  FileText, File, Database, List, Braces, Image, FileCode, FilePenLine,

  // Flow & Logic
  GitBranch, Repeat, ArrowRight, Blend,

  // Form & Input
  Type, Hash, ChevronDown, SquareCheck, ToggleLeft, Edit, Tag,

  // Operations
  Download, Upload, RefreshCw, Calculator, Settings, Code, ListFilter,

  // API & Communication
  Cloud, MessageSquare, Bell,

  // Auth & Commerce
  LogIn, CreditCard, ShoppingCart, Briefcase,

  // AI & Agent
  Brain, Bot, Puzzle, Cpu, Users,

  // Social
  Share2,

  // Utility
  CircleCheck, CirclePlus, CirclePlay, Info, Box, Package, Layers, Camera, X,

  // Layout
  Grid3x3, ChartBar,
} from 'lucide-vue-next'

/**
 * Map of icon name strings to Vue components.
 * Keys must match icon names used in backend CATEGORY_DEFAULTS.
 */
export const iconMap = {
  // Browser & Navigation
  Globe: Navigation,
  Monitor,
  MousePointer,
  MousePointerClick,
  Keyboard,
  Navigation,

  // Time & Scheduling
  Clock,
  Timer,
  Calendar,
  Camera,

  // Files & Data
  File,
  FileText,
  FileCode,
  FilePenLine,
  Database,
  Type,
  List,
  Braces,
  Image,
  Tag,
  Hash,

  // Flow & Logic
  GitBranch,
  Repeat,
  ArrowRight,
  Layers,
  Blend,

  // Form & Input
  ChevronDown,
  SquareCheck,
  ToggleLeft,
  Edit,

  // Operations
  Download,
  Upload,
  RefreshCw,
  Calculator,
  Settings,
  Code,
  ListFilter,
  X,

  // API & Communication
  Cloud,
  MessageSquare,
  Bell,

  // Auth & Commerce
  LogIn,
  CreditCard,
  ShoppingCart,
  Briefcase,

  // AI & Agent
  Brain,
  Bot,
  Puzzle,
  Cpu,
  Users,

  // Social
  Share2,

  // Utility & Validation
  CircleCheck,
  CirclePlus,
  CirclePlay,
  Info,
  Box,
  Package,

  // Layout & Charts
  Grid3x3,
  ChartBar,
}

export default iconMap

import { Platform } from 'react-native';

export const colors = {
  bg: '#060d14',
  bgCard: '#0d1b2a',
  bgCardHover: '#112238',
  bgInput: '#0a1929',
  border: 'rgba(0,201,177,0.18)',
  borderStrong: 'rgba(0,201,177,0.4)',
  teal: '#00c9b1',
  tealDim: 'rgba(0,201,177,0.15)',
  sky: '#38bdf8',
  skyDim: 'rgba(56,189,248,0.15)',
  text: '#e8f4f8',
  textSecondary: '#7ea8bc',
  textDim: '#3d6070',

  tier0: '#22c55e',
  tier0Bg: 'rgba(34,197,94,0.12)',
  tier1: '#38bdf8',
  tier1Bg: 'rgba(56,189,248,0.12)',
  tier2: '#f59e0b',
  tier2Bg: 'rgba(245,158,11,0.12)',
  tier3: '#f97316',
  tier3Bg: 'rgba(249,115,22,0.12)',
  tier4: '#ef4444',
  tier4Bg: 'rgba(239,68,68,0.18)',

  tierColors: ['#22c55e', '#38bdf8', '#f59e0b', '#f97316', '#ef4444'],
  tierBgs: [
    'rgba(34,197,94,0.12)',
    'rgba(56,189,248,0.12)',
    'rgba(245,158,11,0.12)',
    'rgba(249,115,22,0.12)',
    'rgba(239,68,68,0.18)',
  ],
} as const;

export const fonts = {
  serif: Platform.OS === 'web' ? "'Instrument Serif', Georgia, serif" : 'Georgia',
  body: Platform.OS === 'web' ? "'Manrope', system-ui, sans-serif" : 'System',
} as const;

export const radius = {
  sm: 8,
  md: 12,
  lg: 16,
  xl: 22,
  full: 999,
} as const;

export const spacing = {
  xs: 4,
  sm: 8,
  md: 16,
  lg: 24,
  xl: 32,
} as const;

export const tierLabels = [
  'Manage at Home',
  'OTC + Monitor',
  'Doctor / Urgent Care',
  'ER — Same Day',
  'Call 911 Now',
];

export const tierIcons = ['home', 'medkit', 'person', 'hospital', 'alert-circle'];

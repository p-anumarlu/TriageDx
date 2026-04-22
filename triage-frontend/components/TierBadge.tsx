import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { colors, tierLabels, tierIcons, radius } from '../constants/theme';

interface Props {
  level: number;
  large?: boolean;
}

const icons: Array<keyof typeof Ionicons.glyphMap> = [
  'home-outline',
  'medkit-outline',
  'person-outline',
  'hospital-outline',
  'alert-circle',
];

export function TierBadge({ level, large = false }: Props) {
  const l = Math.min(level, 4);
  const color = colors.tierColors[l];
  const bg = colors.tierBgs[l];
  const label = tierLabels[l];

  const dots = [0, 1, 2, 3, 4];

  return (
    <View style={[styles.container, { backgroundColor: bg, borderColor: color + '40' }, large && styles.large]}>
      <View style={[styles.iconCircle, { borderColor: color + '60', backgroundColor: color + '18' }]}>
        <Ionicons name={icons[l]} size={large ? 28 : 18} color={color} />
      </View>
      <View style={styles.text}>
        <Text style={[styles.sublabel, { color: color + 'cc' }, large && styles.sublabelLg]}>
          TRIAGE LEVEL {l + 1} / 5
        </Text>
        <Text style={[styles.label, { color }, large && styles.labelLg]}>{label}</Text>
      </View>
      <View style={styles.dots}>
        {dots.map((i) => (
          <View
            key={i}
            style={[
              styles.dot,
              { backgroundColor: i <= l ? color : color + '25' },
              large && styles.dotLg,
            ]}
          />
        ))}
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flexDirection: 'row',
    alignItems: 'center',
    borderRadius: radius.lg,
    borderWidth: 1,
    padding: 14,
    gap: 12,
  },
  large: {
    padding: 20,
    borderRadius: radius.xl,
  },
  iconCircle: {
    width: 44,
    height: 44,
    borderRadius: 22,
    borderWidth: 1,
    alignItems: 'center',
    justifyContent: 'center',
    flexShrink: 0,
  },
  text: {
    flex: 1,
  },
  sublabel: {
    fontSize: 10,
    fontFamily: 'System',
    fontWeight: '700',
    letterSpacing: 0.8,
    marginBottom: 2,
  },
  sublabelLg: {
    fontSize: 11,
  },
  label: {
    fontSize: 16,
    fontFamily: 'System',
    fontWeight: '600',
  },
  labelLg: {
    fontSize: 20,
  },
  dots: {
    flexDirection: 'row',
    gap: 4,
    alignItems: 'center',
  },
  dot: {
    width: 6,
    height: 6,
    borderRadius: 3,
  },
  dotLg: {
    width: 8,
    height: 8,
    borderRadius: 4,
  },
});

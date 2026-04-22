import React, { useEffect } from 'react';
import {
  View, Text, TouchableOpacity, StyleSheet, SafeAreaView,
} from 'react-native';
import Animated, {
  useSharedValue, useAnimatedStyle, withSpring, withTiming, interpolate,
} from 'react-native-reanimated';
import { router } from 'expo-router';
import Svg, { Ellipse, Path, Line, Circle } from 'react-native-svg';
import { Ionicons } from '@expo/vector-icons';
import { colors, radius, fonts } from '../constants/theme';

interface SubZone {
  id: string;
  label: string;
  sublabel: string;
  icon: keyof typeof Ionicons.glyphMap;
}

const SUB_ZONES: SubZone[] = [
  { id: 'forehead', label: 'Forehead', sublabel: 'Brow area, temples start', icon: 'remove-outline' },
  { id: 'temple',   label: 'Temples',  sublabel: 'Left or right side',       icon: 'arrow-back-outline' },
  { id: 'top',      label: 'Top / Crown', sublabel: 'Top of head',           icon: 'arrow-up-outline' },
  { id: 'back',     label: 'Back of Head', sublabel: 'Occiput, base of skull', icon: 'return-down-back-outline' },
  { id: 'eye_face', label: 'Eye / Face',  sublabel: 'Eye, jaw, cheek',       icon: 'eye-outline' },
];

export default function HeadSubzoneScreen() {
  const scale = useSharedValue(0.85);
  const opacity = useSharedValue(0);

  useEffect(() => {
    scale.value = withSpring(1, { damping: 18, stiffness: 200 });
    opacity.value = withTiming(1, { duration: 280 });
  }, []);

  const containerStyle = useAnimatedStyle(() => ({
    transform: [{ scale: scale.value }],
    opacity: opacity.value,
  }));

  const selectSubzone = (subzoneId: string) => {
    scale.value = withTiming(0.95, { duration: 100 });
    opacity.value = withTiming(0, { duration: 180 });
    setTimeout(() => {
      router.push({
        pathname: '/questions',
        params: { zone: 'head', headSubzone: subzoneId },
      });
    }, 200);
  };

  return (
    <SafeAreaView style={styles.safe}>
      <View style={styles.container}>
        {/* Header */}
        <View style={styles.header}>
          <TouchableOpacity onPress={() => router.back()} style={styles.backBtn}>
            <Ionicons name="arrow-back" size={20} color={colors.teal} />
          </TouchableOpacity>
          <View style={styles.headerText}>
            <Text style={styles.zone}>HEAD</Text>
            <Text style={styles.title}>Where is the problem?</Text>
          </View>
        </View>

        {/* Animated head diagram */}
        <Animated.View style={[styles.svgWrapper, containerStyle]}>
          <Svg viewBox="0 0 200 200" style={styles.svg}>
            {/* Head outline */}
            <Ellipse cx={100} cy={95} rx={62} ry={75} fill="none" stroke="rgba(0,201,177,0.25)" strokeWidth={1} />
            {/* Forehead zone */}
            <Path d="M 48,70 Q 100,40 152,70 L 148,90 Q 100,75 52,90 Z"
              fill="rgba(0,201,177,0.07)" stroke="rgba(0,201,177,0.3)" strokeWidth={0.8} />
            {/* Eye area */}
            <Path d="M 55,95 Q 100,88 145,95 L 142,112 Q 100,107 58,112 Z"
              fill="rgba(56,189,248,0.07)" stroke="rgba(56,189,248,0.25)" strokeWidth={0.8} />
            {/* Top */}
            <Path d="M 52,65 Q 100,22 148,65 Q 100,52 52,65 Z"
              fill="rgba(0,201,177,0.07)" stroke="rgba(0,201,177,0.2)" strokeWidth={0.8} />
            {/* Back hint */}
            <Line x1={100} y1={155} x2={100} y2={168} stroke="rgba(0,201,177,0.4)" strokeWidth={1} strokeDasharray="3,3" />
            {/* Labels */}
            <Ellipse cx={100} cy={57} rx={3} ry={3} fill="rgba(0,201,177,0.5)" />
            <Ellipse cx={68} cy={82} rx={2.5} ry={2.5} fill="rgba(56,189,248,0.5)" />
            <Ellipse cx={132} cy={82} rx={2.5} ry={2.5} fill="rgba(56,189,248,0.5)" />
            <Ellipse cx={100} cy={104} rx={2.5} ry={2.5} fill="rgba(0,201,177,0.4)" />
          </Svg>
        </Animated.View>

        {/* Sub-zone cards */}
        <View style={styles.zones}>
          {SUB_ZONES.map((z, i) => (
            <Animated.View
              key={z.id}
              style={{
                opacity: opacity,
                transform: [{ translateY: interpolate(opacity.value, [0, 1], [10 + i * 5, 0]) }],
              }}
            >
              <TouchableOpacity
                style={styles.zoneCard}
                onPress={() => selectSubzone(z.id)}
                activeOpacity={0.7}
              >
                <View style={styles.zoneIcon}>
                  <Ionicons name={z.icon} size={16} color={colors.teal} />
                </View>
                <View style={styles.zoneText}>
                  <Text style={styles.zoneLabel}>{z.label}</Text>
                  <Text style={styles.zoneSub}>{z.sublabel}</Text>
                </View>
                <Ionicons name="chevron-forward" size={14} color={colors.textDim} />
              </TouchableOpacity>
            </Animated.View>
          ))}
        </View>
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: colors.bg },
  container: { flex: 1, paddingHorizontal: 20 },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingTop: 12,
    paddingBottom: 8,
    gap: 12,
  },
  backBtn: {
    width: 36, height: 36, borderRadius: 18,
    backgroundColor: colors.tealDim,
    alignItems: 'center', justifyContent: 'center',
  },
  headerText: { flex: 1 },
  zone: {
    fontFamily: fonts.body, fontSize: 10, fontWeight: '700',
    color: colors.teal, letterSpacing: 1.5, textTransform: 'uppercase',
  },
  title: { fontFamily: fonts.serif, fontSize: 20, color: colors.text, fontWeight: '400' },
  svgWrapper: { height: 150, alignItems: 'center', justifyContent: 'center', marginBottom: 8 },
  svg: { height: 150, width: 180 },
  zones: { flex: 1, gap: 8 },
  zoneCard: {
    flexDirection: 'row', alignItems: 'center',
    backgroundColor: colors.bgCard,
    borderRadius: radius.md, borderWidth: 1, borderColor: colors.border,
    padding: 13, gap: 12,
  },
  zoneIcon: {
    width: 36, height: 36, borderRadius: 18,
    backgroundColor: colors.tealDim, borderWidth: 1, borderColor: colors.teal + '30',
    alignItems: 'center', justifyContent: 'center',
  },
  zoneText: { flex: 1 },
  zoneLabel: { fontFamily: fonts.body, fontSize: 14, fontWeight: '600', color: colors.text },
  zoneSub: { fontFamily: fonts.body, fontSize: 11, color: colors.textSecondary, marginTop: 1 },
});

import React, { useCallback } from 'react';
import { View, Text, StyleSheet } from 'react-native';
import Svg, {
  Ellipse, Path, G, Rect, Circle,
  Text as SvgText, Defs, LinearGradient, Stop,
} from 'react-native-svg';
import Animated, {
  useSharedValue, useAnimatedProps, withSequence,
  withTiming, interpolateColor,
} from 'react-native-reanimated';
import { colors } from '../constants/theme';

const AnimatedEllipse = Animated.createAnimatedComponent(Ellipse);
const AnimatedPath   = Animated.createAnimatedComponent(Path);

export type ZoneId =
  | 'head' | 'neck' | 'chest' | 'upper_abdomen' | 'lower_abdomen'
  | 'l_arm' | 'r_arm' | 'l_forearm' | 'r_forearm'
  | 'l_hand' | 'r_hand' | 'l_thigh' | 'r_thigh' | 'l_leg' | 'r_leg';

export const ZONE_LABELS: Record<ZoneId, string> = {
  head: 'Head', neck: 'Neck / Throat', chest: 'Chest',
  upper_abdomen: 'Upper Abdomen', lower_abdomen: 'Lower Abdomen',
  l_arm: 'Left Arm', r_arm: 'Right Arm',
  l_forearm: 'Left Forearm', r_forearm: 'Right Forearm',
  l_hand: 'Left Hand', r_hand: 'Right Hand',
  l_thigh: 'Left Thigh', r_thigh: 'Right Thigh',
  l_leg: 'Left Leg', r_leg: 'Right Leg',
};

const IDLE_FILL   = 'rgba(0,201,177,0.05)';
const ACTIVE_FILL = 'rgba(0,201,177,0.28)';
const IDLE_STROKE   = 'rgba(0,201,177,0.22)';
const ACTIVE_STROKE = '#00c9b1';

// Each zone: [path_d or special, label_x, label_y]
const ZONES: Record<ZoneId, { type: 'path' | 'ellipse'; d?: string; cx?: number; cy?: number; rx?: number; ry?: number; lx: number; ly: number; }> = {
  head:           { type: 'ellipse', cx: 100, cy: 48,  rx: 26, ry: 30,  lx: 100, ly: 48 },
  neck:           { type: 'path', d: 'M91,77 L109,77 L111,96 L89,96 Z',  lx: 100, ly: 88 },
  chest:          { type: 'path', d: 'M89,96 L111,96 L134,110 L136,172 L64,172 L66,110 Z', lx: 100, ly: 138 },
  upper_abdomen:  { type: 'path', d: 'M64,172 L136,172 L131,212 L69,212 Z', lx: 100, ly: 192 },
  lower_abdomen:  { type: 'path', d: 'M69,212 L131,212 L126,250 L74,250 Z', lx: 100, ly: 232 },
  r_arm:          { type: 'path', d: 'M50,107 L66,110 L64,172 L46,178 L27,160 L26,118 Z', lx: 45, ly: 143 },
  l_arm:          { type: 'path', d: 'M134,110 L150,107 L174,118 L173,160 L154,178 L136,172 Z', lx: 155, ly: 143 },
  r_forearm:      { type: 'path', d: 'M46,178 L27,162 L24,240 L44,248 Z', lx: 34, ly: 210 },
  l_forearm:      { type: 'path', d: 'M154,178 L173,162 L176,240 L156,248 Z', lx: 166, ly: 210 },
  r_hand:         { type: 'ellipse', cx: 34,  cy: 260, rx: 13, ry: 16, lx: 34,  ly: 260 },
  l_hand:         { type: 'ellipse', cx: 166, cy: 260, rx: 13, ry: 16, lx: 166, ly: 260 },
  r_thigh:        { type: 'path', d: 'M74,250 L100,248 L97,332 L62,328 Z', lx: 78, ly: 292 },
  l_thigh:        { type: 'path', d: 'M100,248 L126,250 L138,328 L103,332 Z', lx: 122, ly: 292 },
  r_leg:          { type: 'path', d: 'M62,330 L97,334 L94,420 L58,416 Z', lx: 76, ly: 378 },
  l_leg:          { type: 'path', d: 'M103,334 L138,330 L142,416 L106,420 Z', lx: 124, ly: 378 },
};

interface ZoneShapeProps {
  zoneId: ZoneId;
  onPress: (id: ZoneId) => void;
}

function ZoneShape({ zoneId, onPress }: ZoneShapeProps) {
  const progress = useSharedValue(0);

  const handlePress = useCallback(() => {
    progress.value = withSequence(
      withTiming(1, { duration: 90 }),
      withTiming(0, { duration: 280 }),
    );
    onPress(zoneId);
  }, [zoneId, onPress]);

  const z = ZONES[zoneId];

  const animatedProps = useAnimatedProps(() => ({
    fill: interpolateColor(progress.value, [0, 1], [IDLE_FILL, ACTIVE_FILL]),
    stroke: interpolateColor(progress.value, [0, 1], [IDLE_STROKE, ACTIVE_STROKE]),
    strokeWidth: 0.8 + progress.value * 0.8,
  }));

  if (z.type === 'ellipse') {
    return (
      <G onPress={handlePress} onClick={handlePress}>
        <AnimatedEllipse
          cx={z.cx} cy={z.cy} rx={z.rx} ry={z.ry}
          animatedProps={animatedProps}
        />
      </G>
    );
  }

  return (
      <G onPress={handlePress} onClick={handlePress}>
        <AnimatedPath
          d={z.d}
          animatedProps={animatedProps}
        />
    </G>
  );
}

interface Props {
  onZonePress: (zoneId: ZoneId) => void;
}

export function BodyDiagram({ onZonePress }: Props) {
  return (
    <View style={styles.container}>
      <Svg viewBox="0 0 200 440" style={styles.svg}>
        <Defs>
          <LinearGradient id="bodyGrad" x1="0" y1="0" x2="0" y2="1">
            <Stop offset="0" stopColor="rgba(0,201,177,0.04)" />
            <Stop offset="1" stopColor="rgba(0,201,177,0.01)" />
          </LinearGradient>
        </Defs>

        {/* Body silhouette outline — faint reference shape */}
        <Path
          d="M100,18 C82,18 74,30 74,48 C74,66 82,76 89,78
             L89,96 C82,98 66,107 50,107 L26,118 L27,160 L46,178
             L44,248 L34,244 L34,276 L44,280 L62,330 L58,416
             L76,420 L94,420 L94,334 L100,332
             L106,334 L106,420 L124,420 L142,416
             L138,330 L156,280 L166,276 L166,244 L156,248
             L176,240 L173,162 L154,178 L136,172
             L134,110 L150,107 L174,118 L173,160 L154,178
             L111,96 C118,76 126,66 126,48 C126,30 118,18 100,18 Z"
          fill="none"
          stroke="rgba(0,201,177,0.10)"
          strokeWidth={0.6}
        />

        {/* Tappable zones */}
        {(Object.keys(ZONES) as ZoneId[]).map((id) => (
          <ZoneShape key={id} zoneId={id} onPress={onZonePress} />
        ))}

        {/* Anatomical division lines — subtle */}
        <Path d="M64,172 L136,172" stroke="rgba(0,201,177,0.12)" strokeWidth={0.5} />
        <Path d="M69,212 L131,212" stroke="rgba(0,201,177,0.12)" strokeWidth={0.5} />
        <Path d="M97,332 L103,332" stroke="rgba(0,201,177,0.12)" strokeWidth={0.5} />

        {/* Centre-line guide */}
        <Path
          d="M100,78 L100,250"
          stroke="rgba(0,201,177,0.08)"
          strokeWidth={0.5}
          strokeDasharray="3,4"
        />

        {/* Zone micro-labels */}
        <SvgText x={100} y={51}  textAnchor="middle" fontSize={6}   fill="rgba(0,201,177,0.55)" fontWeight="600">HEAD</SvgText>
        <SvgText x={100} y={91}  textAnchor="middle" fontSize={5}   fill="rgba(0,201,177,0.45)">NECK</SvgText>
        <SvgText x={100} y={138} textAnchor="middle" fontSize={6}   fill="rgba(0,201,177,0.45)">CHEST</SvgText>
        <SvgText x={100} y={192} textAnchor="middle" fontSize={5.5} fill="rgba(0,201,177,0.40)">UPPER ABD</SvgText>
        <SvgText x={100} y={232} textAnchor="middle" fontSize={5.5} fill="rgba(0,201,177,0.40)">LOWER ABD</SvgText>
        <SvgText x={45}  y={143} textAnchor="middle" fontSize={5}   fill="rgba(0,201,177,0.40)">R ARM</SvgText>
        <SvgText x={155} y={143} textAnchor="middle" fontSize={5}   fill="rgba(0,201,177,0.40)">L ARM</SvgText>
        <SvgText x={34}  y={212} textAnchor="middle" fontSize={4.5} fill="rgba(0,201,177,0.38)">R FORE</SvgText>
        <SvgText x={166} y={212} textAnchor="middle" fontSize={4.5} fill="rgba(0,201,177,0.38)">L FORE</SvgText>
        <SvgText x={34}  y={262} textAnchor="middle" fontSize={4.5} fill="rgba(0,201,177,0.38)">R HAND</SvgText>
        <SvgText x={166} y={262} textAnchor="middle" fontSize={4.5} fill="rgba(0,201,177,0.38)">L HAND</SvgText>
        <SvgText x={78}  y={294} textAnchor="middle" fontSize={5}   fill="rgba(0,201,177,0.40)">R THIGH</SvgText>
        <SvgText x={122} y={294} textAnchor="middle" fontSize={5}   fill="rgba(0,201,177,0.40)">L THIGH</SvgText>
        <SvgText x={76}  y={380} textAnchor="middle" fontSize={5}   fill="rgba(0,201,177,0.40)">R LEG</SvgText>
        <SvgText x={124} y={380} textAnchor="middle" fontSize={5}   fill="rgba(0,201,177,0.40)">L LEG</SvgText>
      </Svg>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, alignItems: 'center', justifyContent: 'center' },
  svg: { height: '100%', maxHeight: 430, width: '100%' },
});

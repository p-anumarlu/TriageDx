import React from 'react';
import { Platform, View, StyleSheet, Text } from 'react-native';
import { colors } from '../constants/theme';

interface Props {
  children: React.ReactNode;
}

export function PhoneFrame({ children }: Props) {
  if (Platform.OS !== 'web') return <>{children}</>;

  return (
    <View style={styles.desktop}>
      <View style={styles.frame}>
        {/* Notch / dynamic island */}
        <View style={styles.notch}>
          <View style={styles.notchPill} />
        </View>
        {/* Status bar */}
        <View style={styles.statusBar}>
          <Text style={styles.statusTime}>9:41</Text>
          <View style={styles.statusRight}>
            <Text style={styles.statusIcon}>●●●</Text>
          </View>
        </View>
        {/* App content */}
        <View style={styles.content}>{children}</View>
        {/* Home indicator */}
        <View style={styles.homeIndicator}>
          <View style={styles.homePill} />
        </View>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  desktop: {
    flex: 1,
    backgroundColor: '#03080f',
    alignItems: 'center',
    justifyContent: 'center',
    minHeight: '100vh' as any,
    paddingVertical: 40,
  },
  frame: {
    width: 390,
    height: 844,
    backgroundColor: colors.bg,
    borderRadius: 50,
    overflow: 'hidden',
    borderWidth: 1.5,
    borderColor: 'rgba(0,201,177,0.2)',
    position: 'relative',
    shadowColor: '#00c9b1',
    shadowOffset: { width: 0, height: 0 },
    shadowOpacity: 0.12,
    shadowRadius: 40,
  } as any,
  notch: {
    position: 'absolute',
    top: 0,
    left: '50%' as any,
    transform: [{ translateX: -60 }],
    width: 120,
    height: 34,
    backgroundColor: '#000',
    borderBottomLeftRadius: 20,
    borderBottomRightRadius: 20,
    zIndex: 10,
    alignItems: 'center',
    justifyContent: 'center',
  },
  notchPill: {
    width: 60,
    height: 14,
    backgroundColor: '#111',
    borderRadius: 10,
    marginTop: 8,
  },
  statusBar: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 24,
    paddingTop: 14,
    paddingBottom: 4,
    height: 50,
  },
  statusTime: {
    color: colors.text,
    fontSize: 13,
    fontFamily: 'System',
    fontWeight: '600',
  },
  statusRight: {
    flexDirection: 'row',
    gap: 4,
  },
  statusIcon: {
    color: colors.text,
    fontSize: 8,
    letterSpacing: 1,
  },
  content: {
    flex: 1,
    overflow: 'hidden' as any,
  },
  homeIndicator: {
    height: 34,
    alignItems: 'center',
    justifyContent: 'center',
  },
  homePill: {
    width: 134,
    height: 5,
    backgroundColor: colors.text,
    borderRadius: 3,
    opacity: 0.3,
  },
});

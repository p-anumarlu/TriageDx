import React from 'react';
import { View, Text, TouchableOpacity, StyleSheet, Linking, Alert } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { Facility } from '../lib/api';
import { colors, radius } from '../constants/theme';

interface Props {
  facility: Facility;
  index: number;
}

export function FacilityCard({ facility, index }: Props) {
  const distText =
    facility.distance_km < 1
      ? `${Math.round(facility.distance_km * 1000)}m away`
      : `${facility.distance_km.toFixed(1)}km away`;

  const handleCall = () => {
    if (!facility.phone) return;
    const tel = `tel:${facility.phone.replace(/\s/g, '')}`;
    Linking.canOpenURL(tel).then((ok) => {
      if (ok) Linking.openURL(tel);
      else Alert.alert('Cannot place call', facility.phone ?? '');
    });
  };

  const handleDirections = () => {
    if (!facility.maps_url) return;
    Linking.openURL(facility.maps_url);
  };

  return (
    <View style={styles.card}>
      <View style={styles.header}>
        <View style={styles.indexCircle}>
          <Text style={styles.indexText}>{index + 1}</Text>
        </View>
        <View style={styles.info}>
          <Text style={styles.name} numberOfLines={1}>{facility.name}</Text>
          <Text style={styles.address} numberOfLines={2}>{facility.address}</Text>
        </View>
        <View style={styles.distBadge}>
          <Text style={styles.distText}>{distText}</Text>
        </View>
      </View>

      <View style={styles.row}>
        {facility.open_now !== undefined && (
          <View style={styles.statusBadge}>
            <View
              style={[
                styles.statusDot,
                { backgroundColor: facility.open_now ? colors.tier0 : colors.tier3 },
              ]}
            />
            <Text style={[styles.statusText, { color: facility.open_now ? colors.tier0 : colors.tier3 }]}>
              {facility.open_now ? 'Open now' : 'Closed'}
            </Text>
          </View>
        )}
        <View style={{ flex: 1 }} />

        {facility.maps_url && (
          <TouchableOpacity style={styles.dirBtn} onPress={handleDirections}>
            <Ionicons name="navigate-outline" size={14} color={colors.sky} />
            <Text style={styles.dirText}>Directions</Text>
          </TouchableOpacity>
        )}

        {facility.phone && (
          <TouchableOpacity style={styles.callBtn} onPress={handleCall}>
            <Ionicons name="call" size={14} color={colors.bg} />
            <Text style={styles.callText}>Call Now</Text>
          </TouchableOpacity>
        )}
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  card: {
    backgroundColor: colors.bgCard,
    borderRadius: radius.md,
    borderWidth: 1,
    borderColor: colors.border,
    padding: 14,
    marginBottom: 10,
    gap: 12,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: 10,
  },
  indexCircle: {
    width: 26,
    height: 26,
    borderRadius: 13,
    backgroundColor: colors.tealDim,
    borderWidth: 1,
    borderColor: colors.teal + '40',
    alignItems: 'center',
    justifyContent: 'center',
    flexShrink: 0,
    marginTop: 1,
  },
  indexText: {
    color: colors.teal,
    fontSize: 11,
    fontWeight: '700',
    fontFamily: 'System',
  },
  info: {
    flex: 1,
    gap: 3,
  },
  name: {
    color: colors.text,
    fontSize: 14,
    fontWeight: '600',
    fontFamily: 'System',
  },
  address: {
    color: colors.textSecondary,
    fontSize: 12,
    fontFamily: 'System',
    lineHeight: 17,
  },
  distBadge: {
    backgroundColor: colors.tealDim,
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: radius.full,
    flexShrink: 0,
  },
  distText: {
    color: colors.teal,
    fontSize: 11,
    fontWeight: '600',
    fontFamily: 'System',
  },
  row: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  statusBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 5,
  },
  statusDot: {
    width: 6,
    height: 6,
    borderRadius: 3,
  },
  statusText: {
    fontSize: 11,
    fontWeight: '600',
    fontFamily: 'System',
  },
  dirBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    paddingHorizontal: 10,
    paddingVertical: 6,
    borderRadius: radius.sm,
    borderWidth: 1,
    borderColor: colors.sky + '40',
    backgroundColor: colors.skyDim,
  },
  dirText: {
    color: colors.sky,
    fontSize: 12,
    fontWeight: '600',
    fontFamily: 'System',
  },
  callBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: radius.sm,
    backgroundColor: colors.teal,
  },
  callText: {
    color: colors.bg,
    fontSize: 12,
    fontWeight: '700',
    fontFamily: 'System',
  },
});

import React, { useEffect, useState } from 'react';
import {
  View, Text, TouchableOpacity, StyleSheet,
  FlatList, SafeAreaView, ActivityIndicator,
} from 'react-native';
import { router, useLocalSearchParams } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import * as Location from 'expo-location';
import { api, Facility, FacilitiesResult } from '../lib/api';
import { FacilityCard } from '../components/FacilityCard';
import { colors, radius, fonts, tierLabels } from '../constants/theme';

export default function FacilitiesScreen() {
  const { triageLevel, sessionId } = useLocalSearchParams<{ triageLevel: string; sessionId: string }>();
  const level = parseInt(triageLevel ?? '2', 10);

  const [result, setResult] = useState<FacilitiesResult | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [locationStatus, setLocationStatus] = useState('Requesting location…');

  useEffect(() => {
    fetchFacilities();
  }, []);

  const fetchFacilities = async () => {
    setLoading(true);
    setError('');
    try {
      const { status } = await Location.requestForegroundPermissionsAsync();
      if (status !== 'granted') {
        setError('Location permission denied. Please enable location access and try again.');
        setLoading(false);
        return;
      }

      setLocationStatus('Getting your location…');
      const loc = await Location.getCurrentPositionAsync({ accuracy: Location.Accuracy.Balanced });
      const { latitude, longitude } = loc.coords;

      setLocationStatus('Finding nearby facilities…');
      const data = await api.getFacilities(latitude, longitude, level);
      setResult(data);
    } catch (e: any) {
      if (e?.response?.status === 503) {
        setError('Facility lookup is temporarily unavailable. Please search manually for nearby medical facilities.');
      } else {
        setError('Could not find nearby facilities. Check your connection and try again.');
      }
    } finally {
      setLoading(false);
    }
  };

  const tierColor = colors.tierColors[Math.min(level, 4)];
  const facilityTypeLabel = result?.facility_type_label ?? tierLabels[level];

  return (
    <SafeAreaView style={styles.safe}>
      <View style={styles.container}>
        {/* Header */}
        <View style={styles.header}>
          <TouchableOpacity style={styles.backBtn} onPress={() => router.back()}>
            <Ionicons name="arrow-back" size={20} color={colors.teal} />
          </TouchableOpacity>
          <View style={styles.headerText}>
            <Text style={[styles.headerLabel, { color: tierColor }]}>
              LEVEL {level + 1} · {tierLabels[Math.min(level, 4)].toUpperCase()}
            </Text>
            <Text style={styles.title}>Nearby {facilityTypeLabel}</Text>
          </View>
        </View>

        {loading ? (
          <View style={styles.center}>
            <ActivityIndicator color={colors.teal} size="large" />
            <Text style={styles.loadingText}>{locationStatus}</Text>
          </View>
        ) : error ? (
          <View style={styles.center}>
            <Ionicons name="location-outline" size={40} color={colors.tier3} />
            <Text style={styles.errorText}>{error}</Text>
            <TouchableOpacity style={styles.retryBtn} onPress={fetchFacilities}>
              <Ionicons name="refresh" size={14} color={colors.bg} />
              <Text style={styles.retryText}>Try Again</Text>
            </TouchableOpacity>
          </View>
        ) : result ? (
          <>
            {/* Source badge */}
            <View style={styles.sourceRow}>
              <View style={styles.sourceBadge}>
                <Ionicons name="locate-outline" size={11} color={colors.textSecondary} />
                <Text style={styles.sourceText}>{result.facilities.length} results · via {result.source}</Text>
              </View>
            </View>

            <FlatList
              data={result.facilities}
              keyExtractor={(_, i) => String(i)}
              renderItem={({ item, index }) => <FacilityCard facility={item} index={index} />}
              contentContainerStyle={styles.listContent}
              showsVerticalScrollIndicator={false}
              ListEmptyComponent={
                <View style={styles.empty}>
                  <Ionicons name="search-outline" size={32} color={colors.textDim} />
                  <Text style={styles.emptyText}>No facilities found nearby. Try expanding your search area.</Text>
                </View>
              }
            />

            {/* Refresh */}
            <TouchableOpacity style={styles.refreshBtn} onPress={fetchFacilities}>
              <Ionicons name="refresh-outline" size={14} color={colors.textSecondary} />
              <Text style={styles.refreshText}>Refresh location</Text>
            </TouchableOpacity>
          </>
        ) : null}

        {/* View summary link */}
        {sessionId && !loading && (
          <TouchableOpacity
            style={styles.summaryLink}
            onPress={() => router.push({ pathname: '/summary', params: { sessionId } })}
          >
            <Ionicons name="document-text-outline" size={14} color={colors.teal} />
            <Text style={styles.summaryLinkText}>View Visit Summary</Text>
          </TouchableOpacity>
        )}
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: colors.bg },
  container: { flex: 1, paddingHorizontal: 20 },
  header: { flexDirection: 'row', alignItems: 'center', paddingTop: 12, paddingBottom: 12, gap: 12 },
  backBtn: { width: 36, height: 36, borderRadius: 18, backgroundColor: colors.tealDim, alignItems: 'center', justifyContent: 'center' },
  headerText: { flex: 1 },
  headerLabel: { fontFamily: fonts.body, fontSize: 10, fontWeight: '700', letterSpacing: 1.2, textTransform: 'uppercase' },
  title: { fontFamily: fonts.serif, fontSize: 20, color: colors.text, fontWeight: '400' },
  center: { flex: 1, alignItems: 'center', justifyContent: 'center', gap: 14 },
  loadingText: { fontFamily: fonts.body, color: colors.textSecondary, fontSize: 13 },
  errorText: { fontFamily: fonts.body, color: colors.tier3, fontSize: 14, textAlign: 'center', lineHeight: 20, maxWidth: 280 },
  retryBtn: { flexDirection: 'row', alignItems: 'center', gap: 6, backgroundColor: colors.teal, paddingHorizontal: 20, paddingVertical: 10, borderRadius: radius.full },
  retryText: { fontFamily: fonts.body, color: colors.bg, fontWeight: '700', fontSize: 13 },
  sourceRow: { marginBottom: 10 },
  sourceBadge: { flexDirection: 'row', alignItems: 'center', gap: 5 },
  sourceText: { fontFamily: fonts.body, fontSize: 11, color: colors.textSecondary },
  listContent: { paddingBottom: 20 },
  empty: { alignItems: 'center', gap: 12, paddingVertical: 40 },
  emptyText: { fontFamily: fonts.body, fontSize: 13, color: colors.textSecondary, textAlign: 'center', maxWidth: 260 },
  refreshBtn: { flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 6, paddingVertical: 10 },
  refreshText: { fontFamily: fonts.body, fontSize: 12, color: colors.textSecondary },
  summaryLink: {
    flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 6,
    paddingVertical: 12, borderTopWidth: 1, borderTopColor: colors.border,
  },
  summaryLinkText: { fontFamily: fonts.body, fontSize: 13, color: colors.teal, fontWeight: '600' },
});

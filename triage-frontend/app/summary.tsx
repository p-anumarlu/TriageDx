import React, { useEffect, useState } from 'react';
import {
  View, Text, TouchableOpacity, StyleSheet, ScrollView,
  SafeAreaView, ActivityIndicator, Platform, Alert,
} from 'react-native';
import { router, useLocalSearchParams } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import * as Sharing from 'expo-sharing';
import * as Clipboard from 'expo-clipboard';
import { api, VisitSummary } from '../lib/api';
import { TierBadge } from '../components/TierBadge';
import { colors, radius, fonts } from '../constants/theme';

export default function SummaryScreen() {
  const { sessionId } = useLocalSearchParams<{ sessionId: string }>();
  const [summary, setSummary] = useState<VisitSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [sharing, setSharing] = useState(false);

  useEffect(() => {
    if (sessionId) loadSummary();
  }, [sessionId]);

  const loadSummary = async () => {
    try {
      const data = await api.getSummary(sessionId!);
      setSummary(data);
    } catch {
      setError('Could not load summary.');
    } finally {
      setLoading(false);
    }
  };

  const handleShare = async () => {
    if (!summary) return;
    setSharing(true);
    try {
      if (Platform.OS !== 'web') {
        const isAvailable = await Sharing.isAvailableAsync();
        if (isAvailable) {
          await Sharing.shareAsync('', { dialogTitle: 'Share Triage Summary' });
          return;
        }
      }
      // Web / fallback — copy to clipboard
      if (typeof navigator !== 'undefined' && navigator.share) {
        await navigator.share({ title: 'triage.ai Visit Summary', text: summary.plain_text });
      } else {
        await Clipboard.setStringAsync(summary.plain_text);
        Alert.alert('Copied', 'Summary copied to clipboard. Paste to share with your doctor or provider.');
      }
    } catch {
      // User cancelled — ignore
    } finally {
      setSharing(false);
    }
  };

  if (loading) {
    return (
      <View style={styles.center}>
        <ActivityIndicator color={colors.teal} size="large" />
        <Text style={styles.loadingText}>Loading summary…</Text>
      </View>
    );
  }

  if (error || !summary) {
    return (
      <View style={styles.center}>
        <Text style={styles.errorText}>{error || 'Summary not available'}</Text>
        <TouchableOpacity onPress={() => router.back()} style={styles.retryBtn}>
          <Text style={styles.retryText}>Go back</Text>
        </TouchableOpacity>
      </View>
    );
  }

  return (
    <SafeAreaView style={styles.safe}>
      <View style={styles.container}>
        {/* Header */}
        <View style={styles.header}>
          <TouchableOpacity style={styles.backBtn} onPress={() => router.back()}>
            <Ionicons name="arrow-back" size={20} color={colors.teal} />
          </TouchableOpacity>
          <Text style={styles.title}>Visit Summary</Text>
          <TouchableOpacity style={styles.shareBtn} onPress={handleShare} disabled={sharing}>
            <Ionicons name={sharing ? 'hourglass-outline' : 'share-outline'} size={18} color={colors.teal} />
          </TouchableOpacity>
        </View>

        <ScrollView style={styles.scroll} showsVerticalScrollIndicator={false} contentContainerStyle={styles.scrollContent}>

          {/* Tier */}
          <TierBadge level={summary.triage_level} large />

          {/* Timestamp & session */}
          <View style={styles.metaRow}>
            <Ionicons name="time-outline" size={13} color={colors.textSecondary} />
            <Text style={styles.metaText}>{summary.timestamp}</Text>
          </View>

          {/* Main fields */}
          {renderField('Body Area', summary.body_area, 'body-outline')}
          {renderField('Main Complaint', summary.main_complaint, 'medical-outline')}
          {renderField('Triage Recommendation', summary.triage_label, 'shield-checkmark-outline')}

          {/* Symptom path */}
          {summary.symptom_path.length > 0 && (
            <View style={styles.card}>
              <View style={styles.cardHeader}>
                <Ionicons name="git-branch-outline" size={14} color={colors.sky} />
                <Text style={[styles.cardLabel, { color: colors.sky }]}>SYMPTOM PATH</Text>
              </View>
              {summary.symptom_path.map((step, i) => (
                <View key={i} style={styles.pathRow}>
                  <View style={styles.pathLine} />
                  <Text style={styles.pathText}>{step}</Text>
                </View>
              ))}
            </View>
          )}

          {/* Red flags */}
          {summary.red_flags_detected.length > 0 && (
            <View style={[styles.card, styles.redCard]}>
              <View style={styles.cardHeader}>
                <Ionicons name="alert-circle" size={14} color={colors.tier4} />
                <Text style={[styles.cardLabel, { color: colors.tier4 }]}>RED FLAGS DETECTED</Text>
              </View>
              {summary.red_flags_detected.map((rf, i) => (
                <View key={i} style={styles.redFlagRow}>
                  <Ionicons name="warning" size={12} color={colors.tier4} />
                  <Text style={styles.redFlagText}>{rf}</Text>
                </View>
              ))}
            </View>
          )}

          {/* Possible conditions */}
          {summary.possible_conditions.length > 0 && (
            <View style={styles.card}>
              <View style={styles.cardHeader}>
                <Ionicons name="clipboard-outline" size={14} color={colors.teal} />
                <Text style={styles.cardLabel}>MAY BE CONSISTENT WITH</Text>
              </View>
              {summary.possible_conditions.map((c, i) => (
                <View key={i} style={styles.condRow}>
                  <View style={styles.condDot} />
                  <Text style={styles.condText}>{c}</Text>
                </View>
              ))}
            </View>
          )}

          {/* Treatment */}
          {summary.treatment_recommendation ? (
            <View style={styles.card}>
              <View style={styles.cardHeader}>
                <Ionicons name="home-outline" size={14} color={colors.tier0} />
                <Text style={[styles.cardLabel, { color: colors.tier0 }]}>TREATMENT GUIDANCE</Text>
              </View>
              <Text style={styles.treatmentText}>{summary.treatment_recommendation}</Text>
            </View>
          ) : null}

          {/* Session ID */}
          <Text style={styles.sessionId}>Session: {summary.session_id.slice(0, 8).toUpperCase()}</Text>

          {/* Disclaimer */}
          <Text style={styles.disclaimer}>{summary.disclaimer}</Text>
        </ScrollView>

        {/* Share button */}
        <TouchableOpacity style={styles.shareBottomBtn} onPress={handleShare} disabled={sharing}>
          <Ionicons name="share-social-outline" size={18} color={colors.bg} />
          <Text style={styles.shareBottomText}>
            {sharing ? 'Sharing…' : 'Share / Present to Doctor'}
          </Text>
        </TouchableOpacity>
      </View>
    </SafeAreaView>
  );
}

function renderField(label: string, value: string, icon: string) {
  return (
    <View style={styles.field} key={label}>
      <View style={styles.fieldHeader}>
        <Ionicons name={icon as any} size={13} color={colors.textSecondary} />
        <Text style={styles.fieldLabel}>{label.toUpperCase()}</Text>
      </View>
      <Text style={styles.fieldValue}>{value}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: colors.bg },
  container: { flex: 1 },
  center: { flex: 1, backgroundColor: colors.bg, alignItems: 'center', justifyContent: 'center', gap: 14, padding: 24 },
  loadingText: { fontFamily: fonts.body, color: colors.textSecondary, fontSize: 14 },
  errorText: { fontFamily: fonts.body, color: colors.tier3, fontSize: 14, textAlign: 'center' },
  retryBtn: { backgroundColor: colors.teal, paddingHorizontal: 24, paddingVertical: 10, borderRadius: radius.full },
  retryText: { fontFamily: fonts.body, color: colors.bg, fontWeight: '700' },
  header: {
    flexDirection: 'row', alignItems: 'center', paddingHorizontal: 20,
    paddingTop: 12, paddingBottom: 8, gap: 12,
  },
  backBtn: { width: 36, height: 36, borderRadius: 18, backgroundColor: colors.tealDim, alignItems: 'center', justifyContent: 'center' },
  title: { flex: 1, fontFamily: fonts.serif, fontSize: 20, color: colors.text, fontWeight: '400' },
  shareBtn: { width: 36, height: 36, borderRadius: 18, backgroundColor: colors.tealDim, alignItems: 'center', justifyContent: 'center' },
  scroll: { flex: 1 },
  scrollContent: { paddingHorizontal: 20, paddingBottom: 20, gap: 10 },
  metaRow: { flexDirection: 'row', alignItems: 'center', gap: 6 },
  metaText: { fontFamily: fonts.body, fontSize: 12, color: colors.textSecondary },
  field: { backgroundColor: colors.bgCard, borderRadius: radius.md, borderWidth: 1, borderColor: colors.border, padding: 13 },
  fieldHeader: { flexDirection: 'row', alignItems: 'center', gap: 6, marginBottom: 5 },
  fieldLabel: { fontFamily: fonts.body, fontSize: 9, fontWeight: '700', color: colors.textSecondary, letterSpacing: 1.2 },
  fieldValue: { fontFamily: fonts.body, fontSize: 14, color: colors.text, lineHeight: 20 },
  card: { backgroundColor: colors.bgCard, borderRadius: radius.md, borderWidth: 1, borderColor: colors.border, padding: 13, gap: 8 },
  redCard: { borderColor: colors.tier4 + '40', backgroundColor: 'rgba(239,68,68,0.06)' },
  cardHeader: { flexDirection: 'row', alignItems: 'center', gap: 7 },
  cardLabel: { fontFamily: fonts.body, fontSize: 9, fontWeight: '700', color: colors.textSecondary, letterSpacing: 1.2, textTransform: 'uppercase' },
  pathRow: { flexDirection: 'row', alignItems: 'flex-start', gap: 10, paddingLeft: 2 },
  pathLine: { width: 2, height: '100%', backgroundColor: colors.sky + '30', borderRadius: 1, marginTop: 6, flexShrink: 0, minHeight: 18 },
  pathText: { fontFamily: fonts.body, fontSize: 12, color: colors.textSecondary, flex: 1, lineHeight: 18 },
  redFlagRow: { flexDirection: 'row', alignItems: 'flex-start', gap: 8 },
  redFlagText: { fontFamily: fonts.body, fontSize: 12, color: colors.tier4, flex: 1, lineHeight: 18 },
  condRow: { flexDirection: 'row', alignItems: 'flex-start', gap: 8 },
  condDot: { width: 5, height: 5, borderRadius: 2.5, backgroundColor: colors.teal, marginTop: 6, flexShrink: 0 },
  condText: { fontFamily: fonts.body, fontSize: 12, color: colors.textSecondary, flex: 1 },
  treatmentText: { fontFamily: fonts.body, fontSize: 13, color: colors.text, lineHeight: 20 },
  sessionId: { fontFamily: fonts.body, fontSize: 10, color: colors.textDim, textAlign: 'center' },
  disclaimer: { fontFamily: fonts.body, fontSize: 10, color: colors.textDim, textAlign: 'center', lineHeight: 15 },
  shareBottomBtn: {
    flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 10,
    backgroundColor: colors.teal, margin: 20, marginTop: 8,
    borderRadius: radius.lg, padding: 15,
  },
  shareBottomText: { fontFamily: fonts.body, fontSize: 15, fontWeight: '700', color: colors.bg },
});

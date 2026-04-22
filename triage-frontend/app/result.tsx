import React, { useEffect, useRef } from 'react';
import {
  View, Text, TouchableOpacity, StyleSheet, ScrollView,
  SafeAreaView, Animated, Linking,
} from 'react-native';
import { router, useLocalSearchParams } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { TierBadge } from '../components/TierBadge';
import { colors, radius, fonts, tierLabels } from '../constants/theme';

export default function ResultScreen() {
  const params = useLocalSearchParams<{
    sessionId: string;
    triageLevel: string;
    triageLabel: string;
    assessment: string;
    treatment: string;
    nextSteps: string;
    conditions: string;
    redFlag: string;
    zone: string;
  }>();

  const level = parseInt(params.triageLevel ?? '0', 10);
  const redFlag = params.redFlag === 'true';
  const nextSteps: string[] = JSON.parse(params.nextSteps ?? '[]');
  const conditions: string[] = JSON.parse(params.conditions ?? '[]');

  const fadeAnim = useRef(new Animated.Value(0)).current;
  const scaleAnim = useRef(new Animated.Value(0.92)).current;
  const pulseAnim = useRef(new Animated.Value(1)).current;

  useEffect(() => {
    Animated.parallel([
      Animated.timing(fadeAnim, { toValue: 1, duration: 400, useNativeDriver: true }),
      Animated.spring(scaleAnim, { toValue: 1, useNativeDriver: true, damping: 16, stiffness: 180 }),
    ]).start();

    if (level === 4) {
      Animated.loop(
        Animated.sequence([
          Animated.timing(pulseAnim, { toValue: 1.06, duration: 700, useNativeDriver: true }),
          Animated.timing(pulseAnim, { toValue: 1, duration: 700, useNativeDriver: true }),
        ])
      ).start();
    }
  }, []);

  // TIER 5 — FULL SCREEN EMERGENCY
  if (level === 4 || redFlag) {
    return (
      <View style={styles.emergency}>
        <Animated.View style={[styles.emergencyInner, { opacity: fadeAnim }]}>
          <Animated.View style={[styles.emergencyIconRing, { transform: [{ scale: pulseAnim }] }]}>
            <Ionicons name="alert-circle" size={48} color={colors.tier4} />
          </Animated.View>
          <Text style={styles.emergencyTitle}>Call 911 Now</Text>
          <Text style={styles.emergencySubtitle}>
            Your symptoms may indicate a life-threatening emergency. Do not wait.
          </Text>
          <Text style={styles.emergencyAssessment}>{params.assessment}</Text>

          <TouchableOpacity
            style={styles.callBtn}
            onPress={() => Linking.openURL('tel:911')}
            activeOpacity={0.85}
          >
            <Ionicons name="call" size={20} color="#fff" />
            <Text style={styles.callText}>Tap to Call 911</Text>
          </TouchableOpacity>

          <View style={styles.emergencySteps}>
            {nextSteps.map((step, i) => (
              <View key={i} style={styles.emergencyStep}>
                <View style={styles.emergencyDot} />
                <Text style={styles.emergencyStepText}>{step}</Text>
              </View>
            ))}
          </View>

          <TouchableOpacity style={styles.emergencyHome} onPress={() => router.replace('/')}>
            <Text style={styles.emergencyHomeText}>Return to home screen</Text>
          </TouchableOpacity>
        </Animated.View>
      </View>
    );
  }

  // TIERS 1–4
  return (
    <SafeAreaView style={styles.safe}>
      <ScrollView style={styles.scroll} contentContainerStyle={styles.scrollContent} showsVerticalScrollIndicator={false}>
        <Animated.View style={{ opacity: fadeAnim, transform: [{ scale: scaleAnim }] }}>

          {/* Back */}
          <TouchableOpacity style={styles.backBtn} onPress={() => router.replace('/')}>
            <Ionicons name="home-outline" size={16} color={colors.teal} />
            <Text style={styles.backText}>New Assessment</Text>
          </TouchableOpacity>

          {/* Tier badge */}
          <TierBadge level={level} large />

          {/* Assessment */}
          <View style={styles.card}>
            <Text style={styles.cardLabel}>ASSESSMENT</Text>
            <Text style={styles.assessmentText}>{params.assessment}</Text>
          </View>

          {/* Conditions */}
          {conditions.length > 0 && (
            <View style={styles.card}>
              <Text style={styles.cardLabel}>MAY BE CONSISTENT WITH</Text>
              {conditions.map((c, i) => (
                <View key={i} style={styles.conditionRow}>
                  <View style={styles.condDot} />
                  <Text style={styles.conditionText}>{c}</Text>
                </View>
              ))}
            </View>
          )}

          {/* Treatment — tiers 0-1 */}
          {level <= 1 && params.treatment ? (
            <View style={[styles.card, styles.treatmentCard]}>
              <View style={styles.treatmentHeader}>
                <Ionicons name="home-outline" size={16} color={colors.tier0} />
                <Text style={[styles.cardLabel, { color: colors.tier0 }]}>HOME TREATMENT</Text>
              </View>
              <Text style={styles.treatmentText}>{params.treatment}</Text>
            </View>
          ) : null}

          {/* Next steps */}
          <View style={styles.card}>
            <Text style={styles.cardLabel}>NEXT STEPS</Text>
            {nextSteps.map((step, i) => (
              <View key={i} style={styles.stepRow}>
                <View style={[styles.stepNum, { backgroundColor: colors.tierColors[level] + '20' }]}>
                  <Text style={[styles.stepNumText, { color: colors.tierColors[level] }]}>{i + 1}</Text>
                </View>
                <Text style={styles.stepText}>{step}</Text>
              </View>
            ))}
          </View>

          {/* CTAs for tiers 2–4 */}
          {level >= 2 && (
            <View style={styles.ctaRow}>
              <TouchableOpacity
                style={styles.ctaPrimary}
                onPress={() => router.push({ pathname: '/facilities', params: { triageLevel: params.triageLevel, sessionId: params.sessionId } })}
              >
                <Ionicons name="location-outline" size={16} color={colors.bg} />
                <Text style={styles.ctaPrimaryText}>Find Nearby {level === 4 ? 'ER' : level === 3 ? 'ER / Urgent Care' : 'Clinic'}</Text>
              </TouchableOpacity>
              <TouchableOpacity
                style={styles.ctaSecondary}
                onPress={() => router.push({ pathname: '/summary', params: { sessionId: params.sessionId } })}
              >
                <Ionicons name="document-text-outline" size={16} color={colors.teal} />
                <Text style={styles.ctaSecondaryText}>View Summary</Text>
              </TouchableOpacity>
            </View>
          )}

          {level <= 1 && (
            <TouchableOpacity
              style={styles.ctaSecondary}
              onPress={() => router.push({ pathname: '/summary', params: { sessionId: params.sessionId } })}
            >
              <Ionicons name="document-text-outline" size={16} color={colors.teal} />
              <Text style={styles.ctaSecondaryText}>View & Share Summary</Text>
            </TouchableOpacity>
          )}

          <Text style={styles.disclaimer}>
            This tool provides general triage guidance only and does not constitute a medical diagnosis. Always consult a licensed healthcare provider.
          </Text>
        </Animated.View>
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: colors.bg },
  scroll: { flex: 1 },
  scrollContent: { padding: 20, gap: 12, paddingBottom: 40 },
  emergency: { flex: 1, backgroundColor: '#0d0305', alignItems: 'center', justifyContent: 'center', padding: 24 },
  emergencyInner: { alignItems: 'center', maxWidth: 340 },
  emergencyIconRing: {
    width: 100, height: 100, borderRadius: 50,
    backgroundColor: 'rgba(239,68,68,0.15)',
    borderWidth: 1.5, borderColor: colors.tier4 + '50',
    alignItems: 'center', justifyContent: 'center', marginBottom: 20,
  },
  emergencyTitle: { fontFamily: fonts.serif, fontSize: 36, color: colors.tier4, fontWeight: '400', marginBottom: 10 },
  emergencySubtitle: { fontFamily: fonts.body, fontSize: 15, color: colors.textSecondary, textAlign: 'center', lineHeight: 22, marginBottom: 12 },
  emergencyAssessment: { fontFamily: fonts.body, fontSize: 13, color: colors.text, textAlign: 'center', lineHeight: 20, marginBottom: 24, opacity: 0.8 },
  callBtn: {
    flexDirection: 'row', alignItems: 'center', gap: 10,
    backgroundColor: colors.tier4, borderRadius: radius.xl,
    paddingVertical: 16, paddingHorizontal: 40, marginBottom: 24,
  },
  callText: { fontFamily: fonts.body, fontSize: 16, fontWeight: '700', color: '#fff' },
  emergencySteps: { gap: 10, width: '100%', marginBottom: 24 },
  emergencyStep: { flexDirection: 'row', alignItems: 'flex-start', gap: 10 },
  emergencyDot: { width: 6, height: 6, borderRadius: 3, backgroundColor: colors.tier4, marginTop: 6, flexShrink: 0 },
  emergencyStepText: { fontFamily: fonts.body, fontSize: 13, color: colors.text, flex: 1, lineHeight: 19 },
  emergencyHome: { padding: 8 },
  emergencyHomeText: { fontFamily: fonts.body, fontSize: 12, color: colors.textSecondary, textDecorationLine: 'underline' },
  backBtn: { flexDirection: 'row', alignItems: 'center', gap: 6, marginBottom: 14 },
  backText: { fontFamily: fonts.body, fontSize: 12, color: colors.teal },
  card: {
    backgroundColor: colors.bgCard, borderRadius: radius.lg,
    borderWidth: 1, borderColor: colors.border, padding: 16, gap: 10,
  },
  treatmentCard: { borderColor: colors.tier0 + '30', backgroundColor: 'rgba(34,197,94,0.06)' },
  treatmentHeader: { flexDirection: 'row', alignItems: 'center', gap: 8 },
  cardLabel: { fontFamily: fonts.body, fontSize: 10, fontWeight: '700', color: colors.textSecondary, letterSpacing: 1.2, textTransform: 'uppercase' },
  assessmentText: { fontFamily: fonts.body, fontSize: 14, color: colors.text, lineHeight: 21 },
  conditionRow: { flexDirection: 'row', alignItems: 'flex-start', gap: 10 },
  condDot: { width: 5, height: 5, borderRadius: 2.5, backgroundColor: colors.teal, marginTop: 7, flexShrink: 0 },
  conditionText: { fontFamily: fonts.body, fontSize: 13, color: colors.textSecondary, flex: 1 },
  treatmentText: { fontFamily: fonts.body, fontSize: 13, color: colors.text, lineHeight: 20 },
  stepRow: { flexDirection: 'row', alignItems: 'flex-start', gap: 10 },
  stepNum: { width: 22, height: 22, borderRadius: 11, alignItems: 'center', justifyContent: 'center', flexShrink: 0 },
  stepNumText: { fontFamily: fonts.body, fontSize: 11, fontWeight: '700' },
  stepText: { fontFamily: fonts.body, fontSize: 13, color: colors.text, flex: 1, lineHeight: 20 },
  ctaRow: { gap: 10 },
  ctaPrimary: {
    flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 8,
    backgroundColor: colors.teal, borderRadius: radius.lg, padding: 15,
  },
  ctaPrimaryText: { fontFamily: fonts.body, fontSize: 14, fontWeight: '700', color: colors.bg },
  ctaSecondary: {
    flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 8,
    backgroundColor: colors.tealDim, borderRadius: radius.lg,
    borderWidth: 1, borderColor: colors.teal + '40', padding: 14,
  },
  ctaSecondaryText: { fontFamily: fonts.body, fontSize: 14, fontWeight: '600', color: colors.teal },
  disclaimer: { fontFamily: fonts.body, fontSize: 10, color: colors.textDim, textAlign: 'center', lineHeight: 15, marginTop: 4 },
});

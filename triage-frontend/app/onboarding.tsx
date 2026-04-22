import React, { useState } from 'react';
import {
  View, Text, TouchableOpacity, StyleSheet, ScrollView,
  SafeAreaView, TextInput, ActivityIndicator,
} from 'react-native';
import { router } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { api } from '../lib/api';
import { colors, radius, fonts } from '../constants/theme';

const STEP_TITLES = ['About You', 'Medical History', 'Medications & Allergies'];
const TOTAL = STEP_TITLES.length;

const CHRONIC_OPTIONS = [
  'Diabetes (Type 1)', 'Diabetes (Type 2)', 'Hypertension', 'Heart Disease',
  'Asthma', 'COPD', 'Chronic Kidney Disease', 'Liver Disease',
  'Cancer (active)', 'HIV / Immunocompromised', 'Thyroid Disease',
  'Depression / Anxiety', 'Epilepsy / Seizures', 'Stroke history',
];

const SURGERY_OPTIONS = [
  'Appendectomy', 'Gallbladder removal', 'Heart bypass / Stent',
  'Hip / Knee replacement', 'Hysterectomy', 'C-section', 'Spinal surgery',
  'Organ transplant', 'Cancer surgery',
];

export default function OnboardingScreen() {
  const [step, setStep] = useState(0);
  const [age, setAge] = useState('');
  const [sex, setSex] = useState<'male' | 'female' | 'other' | ''>('');
  const [conditions, setConditions] = useState<Set<string>>(new Set());
  const [surgeries, setSurgeries] = useState<Set<string>>(new Set());
  const [medications, setMedications] = useState('');
  const [allergies, setAllergies] = useState('');
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');

  const toggle = (set: Set<string>, setter: (s: Set<string>) => void, val: string) => {
    const next = new Set(set);
    next.has(val) ? next.delete(val) : next.add(val);
    setter(next);
  };

  const canAdvance = () => {
    if (step === 0) return age !== '' && sex !== '';
    return true;
  };

  const handleSubmit = async () => {
    setSaving(true);
    setError('');
    try {
      await api.upsertProfile({
        age: parseInt(age, 10),
        biological_sex: sex || undefined,
        chronic_conditions: Array.from(conditions),
        past_surgeries: Array.from(surgeries),
        current_medications: medications
          .split(',').map(s => s.trim()).filter(Boolean),
        allergies: allergies
          .split(',').map(s => s.trim()).filter(Boolean),
      });
      router.replace('/');
    } catch {
      setError('Could not save your profile. You can update it later in Settings.');
      setSaving(false);
    }
  };

  return (
    <SafeAreaView style={styles.safe}>
      <View style={styles.container}>
        {/* Header */}
        <View style={styles.header}>
          <Text style={styles.logo}>triage<Text style={styles.logoAccent}>.ai</Text></Text>
          <Text style={styles.subtitle}>Medical profile helps us give you better triage guidance.</Text>
        </View>

        {/* Progress */}
        <View style={styles.progressRow}>
          {STEP_TITLES.map((t, i) => (
            <View key={i} style={[styles.progressSegment, i <= step && styles.progressSegmentActive]} />
          ))}
        </View>
        <Text style={styles.stepLabel}>{STEP_TITLES[step]} · {step + 1} of {TOTAL}</Text>

        <ScrollView style={styles.scroll} showsVerticalScrollIndicator={false} contentContainerStyle={styles.scrollContent}>

          {/* ── STEP 0: Demographics ── */}
          {step === 0 && (
            <View style={styles.stepContent}>
              <Text style={styles.sectionLabel}>Your age</Text>
              <TextInput
                style={styles.input}
                placeholder="e.g. 34"
                placeholderTextColor={colors.textDim}
                keyboardType="number-pad"
                value={age}
                onChangeText={v => setAge(v.replace(/\D/g, '').slice(0, 3))}
                maxLength={3}
              />

              <Text style={styles.sectionLabel}>Biological sex</Text>
              <Text style={styles.sectionNote}>Used to render an accurate body map and adjust clinical risk factors.</Text>
              <View style={styles.sexRow}>
                {(['male', 'female', 'other'] as const).map(s => (
                  <TouchableOpacity
                    key={s}
                    style={[styles.sexBtn, sex === s && styles.sexBtnActive]}
                    onPress={() => setSex(s)}
                  >
                    <Text style={[styles.sexBtnText, sex === s && styles.sexBtnTextActive]}>
                      {s.charAt(0).toUpperCase() + s.slice(1)}
                    </Text>
                  </TouchableOpacity>
                ))}
              </View>
            </View>
          )}

          {/* ── STEP 1: Medical history ── */}
          {step === 1 && (
            <View style={styles.stepContent}>
              <Text style={styles.sectionLabel}>Chronic conditions (select all that apply)</Text>
              <View style={styles.chipGrid}>
                {CHRONIC_OPTIONS.map(c => (
                  <TouchableOpacity
                    key={c}
                    style={[styles.chip, conditions.has(c) && styles.chipActive]}
                    onPress={() => toggle(conditions, setConditions, c)}
                  >
                    <Text style={[styles.chipText, conditions.has(c) && styles.chipTextActive]}>{c}</Text>
                  </TouchableOpacity>
                ))}
              </View>

              <Text style={[styles.sectionLabel, { marginTop: 20 }]}>Past surgeries</Text>
              <View style={styles.chipGrid}>
                {SURGERY_OPTIONS.map(s => (
                  <TouchableOpacity
                    key={s}
                    style={[styles.chip, surgeries.has(s) && styles.chipActive]}
                    onPress={() => toggle(surgeries, setSurgeries, s)}
                  >
                    <Text style={[styles.chipText, surgeries.has(s) && styles.chipTextActive]}>{s}</Text>
                  </TouchableOpacity>
                ))}
              </View>
            </View>
          )}

          {/* ── STEP 2: Meds & Allergies ── */}
          {step === 2 && (
            <View style={styles.stepContent}>
              <Text style={styles.sectionLabel}>Current medications</Text>
              <Text style={styles.sectionNote}>Separate with commas. Include dosage if known.</Text>
              <TextInput
                style={[styles.input, styles.inputTall]}
                placeholder="e.g. metformin 500mg, lisinopril 10mg, aspirin 81mg"
                placeholderTextColor={colors.textDim}
                value={medications}
                onChangeText={setMedications}
                multiline
                numberOfLines={3}
                textAlignVertical="top"
              />

              <Text style={styles.sectionLabel}>Allergies</Text>
              <Text style={styles.sectionNote}>Medications, foods, or other known allergies.</Text>
              <TextInput
                style={[styles.input, styles.inputTall]}
                placeholder="e.g. penicillin, sulfa drugs, latex, peanuts"
                placeholderTextColor={colors.textDim}
                value={allergies}
                onChangeText={setAllergies}
                multiline
                numberOfLines={2}
                textAlignVertical="top"
              />

              <View style={styles.privacyNote}>
                <Ionicons name="lock-closed-outline" size={12} color={colors.textSecondary} />
                <Text style={styles.privacyText}>
                  This information is stored securely and used only to improve your triage accuracy. It is never sold or shared.
                </Text>
              </View>

              {error ? (
                <View style={styles.errorBox}>
                  <Ionicons name="warning-outline" size={13} color={colors.tier2} />
                  <Text style={styles.errorText}>{error}</Text>
                </View>
              ) : null}
            </View>
          )}
        </ScrollView>

        {/* Navigation buttons */}
        <View style={styles.navRow}>
          {step > 0 ? (
            <TouchableOpacity style={styles.backBtn} onPress={() => setStep(s => s - 1)}>
              <Ionicons name="arrow-back" size={18} color={colors.teal} />
            </TouchableOpacity>
          ) : (
            <TouchableOpacity style={styles.skipBtn} onPress={() => router.replace('/')}>
              <Text style={styles.skipText}>Skip for now</Text>
            </TouchableOpacity>
          )}

          {step < TOTAL - 1 ? (
            <TouchableOpacity
              style={[styles.nextBtn, !canAdvance() && styles.nextBtnDisabled]}
              onPress={() => canAdvance() && setStep(s => s + 1)}
              disabled={!canAdvance()}
            >
              <Text style={[styles.nextText, !canAdvance() && styles.nextTextDisabled]}>Continue</Text>
              <Ionicons name="arrow-forward" size={16} color={canAdvance() ? colors.bg : colors.textDim} />
            </TouchableOpacity>
          ) : (
            <TouchableOpacity
              style={[styles.nextBtn, saving && styles.nextBtnDisabled]}
              onPress={handleSubmit}
              disabled={saving}
            >
              {saving ? <ActivityIndicator color={colors.bg} size="small" /> : null}
              <Text style={styles.nextText}>{saving ? 'Saving…' : 'Save Profile'}</Text>
            </TouchableOpacity>
          )}
        </View>
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: colors.bg },
  container: { flex: 1, paddingHorizontal: 20 },
  header: { paddingTop: 16, paddingBottom: 10, alignItems: 'center' },
  logo: { fontFamily: fonts.serif, fontSize: 26, color: colors.text, fontWeight: '400' },
  logoAccent: { color: colors.teal },
  subtitle: { fontFamily: fonts.body, fontSize: 12, color: colors.textSecondary, textAlign: 'center', marginTop: 4, lineHeight: 18, maxWidth: 280 },
  progressRow: { flexDirection: 'row', gap: 6, marginBottom: 6 },
  progressSegment: { flex: 1, height: 3, borderRadius: 2, backgroundColor: 'rgba(0,201,177,0.15)' },
  progressSegmentActive: { backgroundColor: colors.teal },
  stepLabel: { fontFamily: fonts.body, fontSize: 10, fontWeight: '700', color: colors.textSecondary, textTransform: 'uppercase', letterSpacing: 1.2, marginBottom: 14 },
  scroll: { flex: 1 },
  scrollContent: { paddingBottom: 20 },
  stepContent: { gap: 10 },
  sectionLabel: { fontFamily: fonts.body, fontSize: 11, fontWeight: '700', color: colors.textSecondary, textTransform: 'uppercase', letterSpacing: 1 },
  sectionNote: { fontFamily: fonts.body, fontSize: 11, color: colors.textDim, lineHeight: 16, marginTop: -6 },
  input: {
    backgroundColor: colors.bgCard, borderRadius: radius.md,
    borderWidth: 1, borderColor: colors.border,
    padding: 12, fontFamily: fonts.body, fontSize: 14, color: colors.text,
  },
  inputTall: { minHeight: 76, textAlignVertical: 'top' },
  sexRow: { flexDirection: 'row', gap: 10 },
  sexBtn: {
    flex: 1, paddingVertical: 12, borderRadius: radius.md,
    borderWidth: 1, borderColor: colors.border,
    backgroundColor: colors.bgCard, alignItems: 'center',
  },
  sexBtnActive: { borderColor: colors.teal, backgroundColor: 'rgba(0,201,177,0.08)' },
  sexBtnText: { fontFamily: fonts.body, fontSize: 14, color: colors.textSecondary },
  sexBtnTextActive: { color: colors.teal, fontWeight: '600' },
  chipGrid: { flexDirection: 'row', flexWrap: 'wrap', gap: 8 },
  chip: {
    paddingHorizontal: 12, paddingVertical: 7, borderRadius: radius.full,
    borderWidth: 1, borderColor: colors.border, backgroundColor: colors.bgCard,
  },
  chipActive: { borderColor: colors.teal, backgroundColor: 'rgba(0,201,177,0.08)' },
  chipText: { fontFamily: fonts.body, fontSize: 12, color: colors.textSecondary },
  chipTextActive: { color: colors.teal, fontWeight: '600' },
  privacyNote: {
    flexDirection: 'row', alignItems: 'flex-start', gap: 7,
    backgroundColor: colors.bgCard, borderRadius: radius.md,
    borderWidth: 1, borderColor: colors.border, padding: 12,
  },
  privacyText: { fontFamily: fonts.body, fontSize: 11, color: colors.textSecondary, flex: 1, lineHeight: 17 },
  errorBox: {
    flexDirection: 'row', gap: 8, backgroundColor: colors.tier2Bg,
    borderRadius: radius.md, borderWidth: 1, borderColor: colors.tier2 + '40', padding: 12,
  },
  errorText: { fontFamily: fonts.body, fontSize: 12, color: colors.tier2, flex: 1 },
  navRow: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', paddingVertical: 14, gap: 12 },
  skipBtn: { padding: 8 },
  skipText: { fontFamily: fonts.body, fontSize: 13, color: colors.textSecondary, textDecorationLine: 'underline' },
  backBtn: { width: 40, height: 40, borderRadius: 20, backgroundColor: colors.tealDim, alignItems: 'center', justifyContent: 'center' },
  nextBtn: {
    flex: 1, flexDirection: 'row', alignItems: 'center', justifyContent: 'center',
    gap: 8, backgroundColor: colors.teal, borderRadius: radius.lg, paddingVertical: 14,
  },
  nextBtnDisabled: { backgroundColor: colors.tealDim },
  nextText: { fontFamily: fonts.body, fontSize: 15, fontWeight: '700', color: colors.bg },
  nextTextDisabled: { color: colors.textSecondary },
});

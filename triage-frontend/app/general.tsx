import React, { useState } from 'react';
import {
  View, Text, TouchableOpacity, StyleSheet, ScrollView,
  SafeAreaView, TextInput, ActivityIndicator,
} from 'react-native';
import { router } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { api, AnswerPayload } from '../lib/api';
import { colors, radius, fonts } from '../constants/theme';

interface Symptom {
  id: string;
  label: string;
  sublabel: string;
  icon: keyof typeof Ionicons.glyphMap;
  questionId: string;
  answerValue: string;
}

const SYMPTOMS: Symptom[] = [
  { id: 'fever',     label: 'Fever',              sublabel: 'High temperature or chills',        icon: 'thermometer-outline',    questionId: 'primary', answerValue: 'fever' },
  { id: 'fatigue',   label: 'Extreme Fatigue',    sublabel: 'Unusual weakness or exhaustion',    icon: 'battery-dead-outline',   questionId: 'primary', answerValue: 'fatigue' },
  { id: 'dizzy',     label: 'Dizziness',          sublabel: 'Lightheadedness or vertigo',        icon: 'sync-circle-outline',    questionId: 'primary', answerValue: 'dizzy' },
  { id: 'aches',     label: 'Body Aches',         sublabel: 'Widespread pain or muscle aches',   icon: 'body-outline',           questionId: 'primary', answerValue: 'aches' },
  { id: 'wt_loss',   label: 'Weight Loss',        sublabel: 'Unexplained or unintentional',      icon: 'trending-down-outline',  questionId: 'primary', answerValue: 'wt_loss' },
  { id: 'confusion', label: 'Cognitive Changes',  sublabel: 'Confusion, memory, mood changes',   icon: 'cloudy-outline',         questionId: 'primary', answerValue: 'confusion' },
  // ── new ──
  { id: 'rash',      label: 'Rash / Skin Changes', sublabel: 'Redness, hives, or breakouts',    icon: 'color-palette-outline',  questionId: 'primary', answerValue: 'rash' },
  { id: 'swelling',  label: 'Swelling',            sublabel: 'Puffy skin, face, or limbs',       icon: 'water-outline',          questionId: 'primary', answerValue: 'swelling' },
  { id: 'itching',   label: 'Itching',             sublabel: 'Persistent or widespread itch',    icon: 'hand-left-outline',      questionId: 'primary', answerValue: 'itching' },
  { id: 'nausea',    label: 'Nausea / Vomiting',   sublabel: 'Upset stomach or vomiting',        icon: 'medical-outline',        questionId: 'primary', answerValue: 'nausea' },
];

const DURATION_OPTS = [
  { label: 'Less than 3 days', value: 'acute' },
  { label: '3–7 days',         value: 'week' },
  { label: '1–4 weeks',        value: 'weeks' },
  { label: 'Over 1 month',     value: 'chronic' },
];

const SEVERITY_OPTS = [
  { label: 'Minimal — managing daily activities', value: 'minimal' },
  { label: 'Moderate — noticeably slower',        value: 'mod' },
  { label: 'Significant — mostly resting',        value: 'significant' },
  { label: 'Severe — cannot get out of bed',      value: 'bedbound' },
];

export default function GeneralScreen() {
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const [duration, setDuration] = useState('');
  const [severity, setSeverity] = useState('');
  const [notes, setNotes] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');

  const toggleSymptom = (id: string) => {
    setSelected((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  const canSubmit = selected.size > 0 && duration && severity;

  const handleAssess = async () => {
    if (!canSubmit) return;
    setSubmitting(true);
    setError('');

    const primarySymptom = SYMPTOMS.find((s) => selected.has(s.id));
    const answers: AnswerPayload[] = [
      { question_id: 'primary',  answer_value: primarySymptom?.answerValue ?? 'fatigue' },
      { question_id: 'duration', answer_value: duration },
      { question_id: 'severity', answer_value: severity },
      { question_id: 'assoc',    answer_value: 'none' },
    ];

    // If confusion selected, upgrade assoc answer
    if (selected.has('confusion')) {
      answers[3] = { question_id: 'assoc', answer_value: 'confusion2' };
    }

    try {
      const result = await api.assess({ zone_id: 'general', answers });
      router.push({
        pathname: '/result',
        params: {
          sessionId: result.session_id,
          triageLevel: String(result.triage_level),
          triageLabel: result.triage_label,
          assessment: result.assessment,
          treatment: result.treatment,
          nextSteps: JSON.stringify(result.next_steps),
          conditions: JSON.stringify(result.possible_conditions),
          redFlag: String(result.red_flag),
          zone: 'general',
        },
      });
    } catch {
      setError('Assessment failed. Please check your connection and try again.');
      setSubmitting(false);
    }
  };

  return (
    <SafeAreaView style={styles.safe}>
      <View style={styles.container}>
        {/* Header */}
        <View style={styles.header}>
          <TouchableOpacity style={styles.backBtn} onPress={() => router.back()}>
            <Ionicons name="arrow-back" size={20} color={colors.teal} />
          </TouchableOpacity>
          <View>
            <Text style={styles.zone}>GENERAL / WHOLE BODY</Text>
            <Text style={styles.title}>What are you experiencing?</Text>
          </View>
        </View>

        <ScrollView style={styles.scroll} showsVerticalScrollIndicator={false} contentContainerStyle={styles.scrollContent}>

          {/* AI badge */}
          <View style={styles.aiBadge}>
            <Ionicons name="sparkles" size={12} color={colors.sky} />
            <Text style={styles.aiText}>AI-powered assessment · Powered by Gemini</Text>
          </View>

          {/* Symptom checklist */}
          <Text style={styles.sectionLabel}>Select all that apply</Text>
          <View style={styles.symptomGrid}>
            {SYMPTOMS.map((s) => {
              const active = selected.has(s.id);
              return (
                <TouchableOpacity
                  key={s.id}
                  style={[styles.symptomCard, active && styles.symptomCardActive]}
                  onPress={() => toggleSymptom(s.id)}
                  activeOpacity={0.75}
                >
                  <View style={[styles.symptomIcon, active && styles.symptomIconActive]}>
                    <Ionicons name={s.icon} size={18} color={active ? colors.bg : colors.teal} />
                  </View>
                  <Text style={[styles.symptomLabel, active && styles.symptomLabelActive]}>{s.label}</Text>
                  <Text style={[styles.symptomSub, active && styles.symptomSubActive]}>{s.sublabel}</Text>
                  {active && (
                    <View style={styles.checkMark}>
                      <Ionicons name="checkmark" size={10} color={colors.bg} />
                    </View>
                  )}
                </TouchableOpacity>
              );
            })}
          </View>

          {/* Duration */}
          <Text style={styles.sectionLabel}>How long has this been going on?</Text>
          <View style={styles.optionList}>
            {DURATION_OPTS.map((o) => (
              <TouchableOpacity
                key={o.value}
                style={[styles.optionBtn, duration === o.value && styles.optionBtnActive]}
                onPress={() => setDuration(o.value)}
                activeOpacity={0.75}
              >
                <View style={[styles.radio, duration === o.value && styles.radioActive]}>
                  {duration === o.value && <View style={styles.radioInner} />}
                </View>
                <Text style={[styles.optionText, duration === o.value && styles.optionTextActive]}>
                  {o.label}
                </Text>
              </TouchableOpacity>
            ))}
          </View>

          {/* Severity */}
          <Text style={styles.sectionLabel}>How much is this affecting your daily function?</Text>
          <View style={styles.optionList}>
            {SEVERITY_OPTS.map((o) => (
              <TouchableOpacity
                key={o.value}
                style={[styles.optionBtn, severity === o.value && styles.optionBtnActive]}
                onPress={() => setSeverity(o.value)}
                activeOpacity={0.75}
              >
                <View style={[styles.radio, severity === o.value && styles.radioActive]}>
                  {severity === o.value && <View style={styles.radioInner} />}
                </View>
                <Text style={[styles.optionText, severity === o.value && styles.optionTextActive]}>
                  {o.label}
                </Text>
              </TouchableOpacity>
            ))}
          </View>

          {/* Free text notes */}
          <Text style={styles.sectionLabel}>Additional details (optional)</Text>
          <TextInput
            style={styles.textInput}
            placeholder="Describe any other symptoms, medications, or context…"
            placeholderTextColor={colors.textDim}
            value={notes}
            onChangeText={setNotes}
            multiline
            numberOfLines={3}
            textAlignVertical="top"
          />

          {/* Error */}
          {error ? (
            <View style={styles.errorBox}>
              <Ionicons name="warning-outline" size={14} color={colors.tier3} />
              <Text style={styles.errorText}>{error}</Text>
            </View>
          ) : null}

          {/* Submit */}
          <TouchableOpacity
            style={[styles.assessBtn, (!canSubmit || submitting) && styles.assessBtnDisabled]}
            onPress={handleAssess}
            disabled={!canSubmit || submitting}
            activeOpacity={0.8}
          >
            {submitting ? (
              <>
                <ActivityIndicator color={colors.bg} size="small" />
                <Text style={styles.assessBtnText}>Analysing with AI…</Text>
              </>
            ) : (
              <>
                <Ionicons name="shield-checkmark-outline" size={18} color={canSubmit ? colors.bg : colors.textDim} />
                <Text style={[styles.assessBtnText, !canSubmit && styles.assessBtnTextDisabled]}>
                  Assess Symptoms
                </Text>
              </>
            )}
          </TouchableOpacity>

          {!canSubmit && (
            <Text style={styles.hint}>
              Select at least one symptom, duration, and severity to continue
            </Text>
          )}

          <Text style={styles.disclaimer}>
            This tool provides triage guidance only and does not constitute a medical diagnosis.
          </Text>
        </ScrollView>
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: colors.bg },
  container: { flex: 1 },
  header: {
    flexDirection: 'row', alignItems: 'center',
    paddingHorizontal: 20, paddingTop: 12, paddingBottom: 10, gap: 12,
  },
  backBtn: {
    width: 36, height: 36, borderRadius: 18,
    backgroundColor: colors.tealDim, alignItems: 'center', justifyContent: 'center',
  },
  zone: { fontFamily: fonts.body, fontSize: 10, fontWeight: '700', color: colors.teal, letterSpacing: 1.2, textTransform: 'uppercase' },
  title: { fontFamily: fonts.serif, fontSize: 20, color: colors.text, fontWeight: '400' },
  scroll: { flex: 1 },
  scrollContent: { paddingHorizontal: 20, paddingBottom: 40, gap: 12 },
  aiBadge: {
    flexDirection: 'row', alignItems: 'center', gap: 6,
    backgroundColor: colors.skyDim, borderWidth: 1, borderColor: colors.sky + '30',
    borderRadius: radius.full, paddingHorizontal: 12, paddingVertical: 6, alignSelf: 'flex-start',
  },
  aiText: { fontFamily: fonts.body, fontSize: 11, fontWeight: '600', color: colors.sky },
  sectionLabel: {
    fontFamily: fonts.body, fontSize: 11, fontWeight: '700',
    color: colors.textSecondary, letterSpacing: 0.8, textTransform: 'uppercase',
  },
  symptomGrid: { flexDirection: 'row', flexWrap: 'wrap', gap: 8 },
  symptomCard: {
    width: '47%', backgroundColor: colors.bgCard,
    borderRadius: radius.md, borderWidth: 1, borderColor: colors.border,
    padding: 13, gap: 4, position: 'relative',
  },
  symptomCardActive: { borderColor: colors.teal, backgroundColor: 'rgba(0,201,177,0.08)' },
  symptomIcon: {
    width: 34, height: 34, borderRadius: 17,
    backgroundColor: colors.tealDim, alignItems: 'center', justifyContent: 'center', marginBottom: 4,
  },
  symptomIconActive: { backgroundColor: colors.teal },
  symptomLabel: { fontFamily: fonts.body, fontSize: 13, fontWeight: '600', color: colors.text },
  symptomLabelActive: { color: colors.teal },
  symptomSub: { fontFamily: fonts.body, fontSize: 10, color: colors.textSecondary, lineHeight: 14 },
  symptomSubActive: { color: colors.teal + 'aa' },
  checkMark: {
    position: 'absolute', top: 8, right: 8,
    width: 16, height: 16, borderRadius: 8,
    backgroundColor: colors.teal, alignItems: 'center', justifyContent: 'center',
  },
  optionList: { gap: 8 },
  optionBtn: {
    flexDirection: 'row', alignItems: 'center', gap: 12,
    backgroundColor: colors.bgCard, borderRadius: radius.md,
    borderWidth: 1, borderColor: colors.border, padding: 13,
  },
  optionBtnActive: { borderColor: colors.teal, backgroundColor: 'rgba(0,201,177,0.06)' },
  radio: {
    width: 18, height: 18, borderRadius: 9,
    borderWidth: 1.5, borderColor: colors.textDim,
    alignItems: 'center', justifyContent: 'center', flexShrink: 0,
  },
  radioActive: { borderColor: colors.teal },
  radioInner: { width: 8, height: 8, borderRadius: 4, backgroundColor: colors.teal },
  optionText: { fontFamily: fonts.body, fontSize: 13, color: colors.textSecondary, flex: 1, lineHeight: 19 },
  optionTextActive: { color: colors.text },
  textInput: {
    backgroundColor: colors.bgInput, borderRadius: radius.md,
    borderWidth: 1, borderColor: colors.border,
    padding: 13, fontFamily: fonts.body, fontSize: 13,
    color: colors.text, minHeight: 80, lineHeight: 20,
  },
  errorBox: {
    flexDirection: 'row', alignItems: 'flex-start', gap: 8,
    backgroundColor: 'rgba(249,115,22,0.08)', borderRadius: radius.md,
    borderWidth: 1, borderColor: colors.tier3 + '40', padding: 12,
  },
  errorText: { fontFamily: fonts.body, fontSize: 12, color: colors.tier3, flex: 1, lineHeight: 18 },
  assessBtn: {
    flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 10,
    backgroundColor: colors.teal, borderRadius: radius.lg, padding: 16,
  },
  assessBtnDisabled: { backgroundColor: colors.tealDim, borderWidth: 1, borderColor: colors.teal + '30' },
  assessBtnText: { fontFamily: fonts.body, fontSize: 15, fontWeight: '700', color: colors.bg },
  assessBtnTextDisabled: { color: colors.textSecondary },
  hint: { fontFamily: fonts.body, fontSize: 11, color: colors.textDim, textAlign: 'center' },
  disclaimer: { fontFamily: fonts.body, fontSize: 10, color: colors.textDim, textAlign: 'center', lineHeight: 15 },
});

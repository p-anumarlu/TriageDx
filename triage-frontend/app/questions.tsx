import React, { useEffect, useState, useRef } from 'react';
import {
  View, Text, TouchableOpacity, StyleSheet, ScrollView,
  SafeAreaView, ActivityIndicator, TextInput, Keyboard,
} from 'react-native';
import Animated, {
  useSharedValue, useAnimatedStyle,
  withTiming, withSpring, withSequence,
} from 'react-native-reanimated';
import { router, useLocalSearchParams } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { api, AnswerPayload, FlowTree, FlowNode, FlowOption, AssessResult } from '../lib/api';
import { ImageUploader, VisionResult } from '../components/ImageUploader';
import { colors, radius, fonts } from '../constants/theme';
import { ZONE_LABELS } from '../components/BodyDiagram';

export default function QuestionsScreen() {
  const { zone, headSubzone } = useLocalSearchParams<{ zone: string; headSubzone?: string }>();

  const [flow, setFlow] = useState<FlowTree | null>(null);
  const [nodeId, setNodeId] = useState('start');
  const [answers, setAnswers] = useState<AnswerPayload[]>([]);
  const [notes, setNotes] = useState('');
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');
  const [visionResult, setVisionResult] = useState<VisionResult | null>(null);
  const [otherOpen, setOtherOpen] = useState(false);
  const [otherText, setOtherText] = useState('');

  const fadeAnim  = useSharedValue(1);
  const slideAnim = useSharedValue(0);

  useEffect(() => { loadFlow(); }, [zone]);

  const loadFlow = async () => {
    try {
      const data = await api.getQuestions(zone ?? 'chest');
      setFlow(data.flow);
      if (headSubzone && data.flow['start']) {
        const opt = data.flow['start'].options.find(o => o.value === headSubzone);
        if (opt) {
          setAnswers([{ question_id: 'start', answer_value: opt.value }]);
          setNodeId(opt.next_node ?? 'start');
        }
      }
    } catch {
      setError('Could not load questions. Is the backend running on port 8000?');
    } finally {
      setLoading(false);
    }
  };

  const animateTransition = (callback: () => void) => {
    fadeAnim.value  = withTiming(0,  { duration: 110 });
    slideAnim.value = withTiming(-14, { duration: 110 });
    setTimeout(() => {
      callback();
      slideAnim.value = 16;
      fadeAnim.value  = withSpring(1, { damping: 22, stiffness: 260 });
      slideAnim.value = withSpring(0, { damping: 22, stiffness: 260 });
    }, 120);
  };

  const handleOption = async (opt: FlowOption) => {
    setOtherOpen(false);
    const newAnswers: AnswerPayload[] = [
      ...answers,
      { question_id: nodeId, answer_value: opt.value },
    ];
    if (opt.red_flag || opt.next_node === null) {
      await submitAssessment(newAnswers);
      return;
    }
    animateTransition(() => {
      setAnswers(newAnswers);
      setNodeId(opt.next_node!);
    });
  };

  // "Other" path — treat as urgency-neutral skip, accumulate note, advance to next reachable node
  const handleOtherSubmit = async () => {
    Keyboard.dismiss();
    if (!flow) return;
    const currentNode = flow[nodeId];
    if (!currentNode) return;

    // Append to running notes
    const combinedNotes = [notes, otherText].filter(Boolean).join(' | ');
    setNotes(combinedNotes);
    setOtherText('');
    setOtherOpen(false);

    const newAnswers: AnswerPayload[] = [
      ...answers,
      { question_id: nodeId, answer_value: 'other' },
    ];

    // Find a safe next node: prefer a "none" option, otherwise pick first non-red-flag option's next
    const noneOpt = currentNode.options.find(o => ['none', 'no', 'neither', 'normal'].includes(o.value));
    const firstSafe = currentNode.options.find(o => !o.red_flag);
    const nextTarget = noneOpt ?? firstSafe;

    if (!nextTarget || nextTarget.next_node === null) {
      await submitAssessment(newAnswers, combinedNotes);
    } else {
      animateTransition(() => {
        setAnswers(newAnswers);
        setNodeId(nextTarget.next_node!);
      });
    }
  };

  const submitAssessment = async (
    finalAnswers: AnswerPayload[],
    finalNotes: string = notes,
  ) => {
    setSubmitting(true);
    try {
      const result: AssessResult = await api.assess({
        zone_id: zone ?? 'chest',
        answers: finalAnswers,
        notes: finalNotes || undefined,
      });
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
          zone: zone ?? '',
          visionSignal: visionResult ? String(visionResult.urgency_signal) : '',
        },
      });
    } catch {
      setError('Assessment failed. Please check your connection and try again.');
      setSubmitting(false);
    }
  };

  const cardStyle = useAnimatedStyle(() => ({
    opacity: fadeAnim.value,
    transform: [{ translateY: slideAnim.value }],
  }));

  if (loading) {
    return (
      <View style={styles.center}>
        <ActivityIndicator color={colors.teal} size="large" />
        <Text style={styles.loadingText}>Loading questions…</Text>
      </View>
    );
  }

  if (error) {
    return (
      <View style={styles.center}>
        <Ionicons name="warning-outline" size={40} color={colors.tier3} />
        <Text style={styles.errorText}>{error}</Text>
        <TouchableOpacity
          style={styles.retryBtn}
          onPress={() => { setError(''); setLoading(true); loadFlow(); }}
        >
          <Text style={styles.retryText}>Retry</Text>
        </TouchableOpacity>
      </View>
    );
  }

  if (!flow) return null;

  const currentNode: FlowNode | undefined = flow[nodeId];
  if (!currentNode) {
    return (
      <View style={styles.center}>
        <Text style={styles.errorText}>Flow error — node "{nodeId}" not found</Text>
      </View>
    );
  }

  const progress  = Math.min(answers.length / 5, 0.94);
  const zoneLabel = ZONE_LABELS[zone as keyof typeof ZONE_LABELS] ?? zone;

  return (
    <SafeAreaView style={styles.safe}>
      <View style={styles.container}>

        {/* Top bar */}
        <View style={styles.topBar}>
          <TouchableOpacity style={styles.backBtn} onPress={() => router.back()}>
            <Ionicons name="arrow-back" size={20} color={colors.teal} />
          </TouchableOpacity>
          <View style={styles.topMeta}>
            <Text style={styles.zoneLabel}>{zoneLabel}</Text>
            <Text style={styles.stepCount}>Step {answers.length + 1}</Text>
          </View>
          {notes.length > 0 && (
            <View style={styles.notesPill}>
              <Ionicons name="document-text-outline" size={11} color={colors.sky} />
              <Text style={styles.notesPillText}>Notes added</Text>
            </View>
          )}
        </View>

        {/* Progress bar */}
        <View style={styles.progressTrack}>
          <Animated.View
            style={[
              styles.progressFill,
              { width: `${Math.round(progress * 100)}%` as any },
            ]}
          />
        </View>

        <ScrollView
          style={styles.scroll}
          showsVerticalScrollIndicator={false}
          keyboardShouldPersistTaps="handled"
        >
          <Animated.View style={[styles.questionWrap, cardStyle]}>

            {/* Question text */}
            <Text style={styles.question}>{currentNode.question}</Text>

            {/* Answer options */}
            <View style={styles.options}>
              {currentNode.options.map((opt, idx) => (
                <OptionCard
                  key={opt.value}
                  opt={opt}
                  index={idx}
                  disabled={submitting}
                  onPress={() => handleOption(opt)}
                />
              ))}
            </View>

            {/* ── OTHER / NONE OF THESE ── */}
            <View style={styles.otherSection}>
              {!otherOpen ? (
                <TouchableOpacity
                  style={styles.otherCollapsed}
                  onPress={() => setOtherOpen(true)}
                  activeOpacity={0.7}
                >
                  <Ionicons name="add-circle-outline" size={16} color={colors.textSecondary} />
                  <Text style={styles.otherCollapsedText}>
                    Other / None of these / Add more details
                  </Text>
                  <Ionicons name="chevron-down" size={13} color={colors.textDim} />
                </TouchableOpacity>
              ) : (
                <View style={styles.otherExpanded}>
                  <View style={styles.otherHeader}>
                    <Ionicons name="create-outline" size={14} color={colors.sky} />
                    <Text style={styles.otherHeaderText}>Describe in your own words</Text>
                    <TouchableOpacity onPress={() => { setOtherOpen(false); setOtherText(''); }}>
                      <Ionicons name="close" size={16} color={colors.textDim} />
                    </TouchableOpacity>
                  </View>
                  <TextInput
                    style={styles.otherInput}
                    placeholder="e.g. The pain is behind my left ear and started after a cold…"
                    placeholderTextColor={colors.textDim}
                    value={otherText}
                    onChangeText={setOtherText}
                    multiline
                    numberOfLines={3}
                    textAlignVertical="top"
                    autoFocus
                  />
                  <View style={styles.otherActions}>
                    <Text style={styles.otherHint}>
                      Your description will be included in the assessment.
                    </Text>
                    <TouchableOpacity
                      style={[
                        styles.otherSubmitBtn,
                        !otherText.trim() && styles.otherSubmitBtnDisabled,
                      ]}
                      onPress={handleOtherSubmit}
                      disabled={!otherText.trim() || submitting}
                    >
                      <Text
                        style={[
                          styles.otherSubmitText,
                          !otherText.trim() && styles.otherSubmitTextDisabled,
                        ]}
                      >
                        Continue with this
                      </Text>
                      <Ionicons
                        name="arrow-forward"
                        size={14}
                        color={otherText.trim() ? colors.bg : colors.textDim}
                      />
                    </TouchableOpacity>
                  </View>
                </View>
              )}
            </View>

            {/* Image upload — first question only */}
            {answers.length === 0 && (
              <View style={styles.imageSection}>
                <ImageUploader
                  zoneId={zone ?? 'unknown'}
                  onResult={setVisionResult}
                />
              </View>
            )}

            {/* Vision red flag banner */}
            {visionResult?.red_flag_visible && (
              <View style={styles.visionRedFlag}>
                <Ionicons name="alert-circle" size={14} color={colors.tier4} />
                <Text style={styles.visionRedFlagText}>
                  Photo analysis flagged a possible emergency. Complete the questions to confirm.
                </Text>
              </View>
            )}

          </Animated.View>
        </ScrollView>

        {/* Submitting overlay */}
        {submitting && (
          <View style={styles.submittingOverlay}>
            <ActivityIndicator color={colors.teal} size="small" />
            <Text style={styles.submittingText}>Analysing symptoms…</Text>
          </View>
        )}

        <Text style={styles.disclaimer}>
          Triage guidance only · Not a medical diagnosis
        </Text>
      </View>
    </SafeAreaView>
  );
}

function OptionCard({
  opt, index, disabled, onPress,
}: {
  opt: FlowOption;
  index: number;
  disabled: boolean;
  onPress: () => void;
}) {
  const scale = useSharedValue(1);
  const pressed = useSharedValue(0);

  const handlePress = () => {
    scale.value = withSequence(
      withTiming(0.97, { duration: 80 }),
      withSpring(1, { damping: 18 }),
    );
    pressed.value = withSequence(
      withTiming(1, { duration: 80 }),
      withTiming(0, { duration: 300 }),
    );
    onPress();
  };

  const animStyle = useAnimatedStyle(() => ({
    transform: [{ scale: scale.value }],
    opacity: withTiming(1, { duration: 180 + index * 40 }),
  }));

  return (
    <Animated.View
      style={[
        styles.optionCard,
        opt.red_flag && styles.optionCardRed,
        animStyle,
      ]}
    >
      <TouchableOpacity
        style={styles.optionInner}
        onPress={handlePress}
        disabled={disabled}
        activeOpacity={0.72}
      >
        {opt.red_flag && (
          <Ionicons name="alert-circle" size={15} color={colors.tier4} />
        )}
        <Text style={[styles.optionText, opt.red_flag && styles.optionTextRed]}>
          {opt.label}
        </Text>
        <Ionicons name="chevron-forward" size={13} color={colors.textDim} />
      </TouchableOpacity>
    </Animated.View>
  );
}

const styles = StyleSheet.create({
  safe:        { flex: 1, backgroundColor: colors.bg },
  container:   { flex: 1, paddingHorizontal: 20, paddingBottom: 12 },
  center:      { flex: 1, backgroundColor: colors.bg, alignItems: 'center', justifyContent: 'center', gap: 14, padding: 24 },
  loadingText: { fontFamily: fonts.body, color: colors.textSecondary, fontSize: 14 },
  errorText:   { fontFamily: fonts.body, color: colors.tier3, fontSize: 14, textAlign: 'center', lineHeight: 20 },
  retryBtn:    { backgroundColor: colors.teal, paddingHorizontal: 24, paddingVertical: 10, borderRadius: radius.full },
  retryText:   { fontFamily: fonts.body, color: colors.bg, fontWeight: '700', fontSize: 14 },

  topBar:   { flexDirection: 'row', alignItems: 'center', paddingTop: 12, paddingBottom: 10, gap: 12 },
  backBtn:  { width: 36, height: 36, borderRadius: 18, backgroundColor: colors.tealDim, alignItems: 'center', justifyContent: 'center' },
  topMeta:  { flex: 1 },
  zoneLabel: { fontFamily: fonts.body, fontSize: 10, fontWeight: '700', color: colors.teal, textTransform: 'uppercase', letterSpacing: 1.2 },
  stepCount: { fontFamily: fonts.body, fontSize: 12, color: colors.textSecondary, marginTop: 1 },
  notesPill: { flexDirection: 'row', alignItems: 'center', gap: 4, backgroundColor: colors.skyDim, borderRadius: radius.full, paddingHorizontal: 8, paddingVertical: 3 },
  notesPillText: { fontFamily: fonts.body, fontSize: 10, color: colors.sky, fontWeight: '600' },

  progressTrack: { height: 3, backgroundColor: 'rgba(0,201,177,0.15)', borderRadius: 2, marginBottom: 20, overflow: 'hidden' },
  progressFill:  { height: '100%', backgroundColor: colors.teal, borderRadius: 2 },

  scroll:       { flex: 1 },
  questionWrap: { paddingBottom: 24 },
  question:     { fontFamily: fonts.serif, fontSize: 22, color: colors.text, fontWeight: '400', lineHeight: 30, marginBottom: 22 },
  options:      { gap: 9 },

  optionCard: {
    borderRadius: radius.md,
    borderWidth: 1,
    borderColor: colors.border,
    overflow: 'hidden',
    backgroundColor: colors.bgCard,
  },
  optionCardRed: { borderColor: colors.tier4 + '40', backgroundColor: colors.tier4Bg },
  optionInner:   { flexDirection: 'row', alignItems: 'center', paddingVertical: 14, paddingHorizontal: 16, gap: 10 },
  optionText:    { fontFamily: fonts.body, fontSize: 14, color: colors.text, flex: 1, lineHeight: 20 },
  optionTextRed: { color: colors.tier4 },

  // ── Other section ──────────────────────────────────────────────────────────
  otherSection: { marginTop: 12 },

  otherCollapsed: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 9,
    paddingVertical: 11,
    paddingHorizontal: 14,
    borderRadius: radius.md,
    borderWidth: 1,
    borderStyle: 'dashed' as any,
    borderColor: colors.border,
  },
  otherCollapsedText: {
    fontFamily: fonts.body,
    fontSize: 13,
    color: colors.textSecondary,
    flex: 1,
  },

  otherExpanded: {
    borderRadius: radius.md,
    borderWidth: 1,
    borderColor: colors.sky + '40',
    backgroundColor: colors.bgCard,
    padding: 13,
    gap: 10,
  },
  otherHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 7,
  },
  otherHeaderText: {
    fontFamily: fonts.body,
    fontSize: 12,
    fontWeight: '600',
    color: colors.sky,
    flex: 1,
  },
  otherInput: {
    backgroundColor: colors.bg,
    borderRadius: radius.sm,
    borderWidth: 1,
    borderColor: colors.border,
    padding: 11,
    fontFamily: fonts.body,
    fontSize: 13,
    color: colors.text,
    minHeight: 80,
    lineHeight: 20,
  },
  otherActions: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
  },
  otherHint: {
    fontFamily: fonts.body,
    fontSize: 10,
    color: colors.textDim,
    flex: 1,
    lineHeight: 14,
  },
  otherSubmitBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    backgroundColor: colors.teal,
    paddingHorizontal: 14,
    paddingVertical: 8,
    borderRadius: radius.md,
  },
  otherSubmitBtnDisabled: {
    backgroundColor: colors.tealDim,
  },
  otherSubmitText: {
    fontFamily: fonts.body,
    fontSize: 12,
    fontWeight: '700',
    color: colors.bg,
  },
  otherSubmitTextDisabled: {
    color: colors.textSecondary,
  },

  imageSection: { marginTop: 16 },

  visionRedFlag: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: 8,
    marginTop: 12,
    backgroundColor: colors.tier4Bg,
    borderRadius: radius.md,
    borderWidth: 1,
    borderColor: colors.tier4 + '40',
    padding: 12,
  },
  visionRedFlagText: {
    fontFamily: fonts.body,
    fontSize: 12,
    color: colors.tier4,
    flex: 1,
    lineHeight: 18,
  },

  submittingOverlay: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: colors.bgCard,
    borderRadius: radius.md,
    borderWidth: 1,
    borderColor: colors.teal + '30',
    padding: 14,
    gap: 10,
    marginBottom: 8,
  },
  submittingText: { fontFamily: fonts.body, color: colors.teal, fontSize: 13 },
  disclaimer:     { fontFamily: fonts.body, fontSize: 10, color: colors.textDim, textAlign: 'center' },
});

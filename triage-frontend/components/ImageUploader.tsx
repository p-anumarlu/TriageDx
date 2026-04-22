import React, { useState } from 'react';
import {
  View, Text, TouchableOpacity, StyleSheet,
  Image, ActivityIndicator, Platform, Alert,
} from 'react-native';
import * as ImagePicker from 'expo-image-picker';
import { Ionicons } from '@expo/vector-icons';
import axios from 'axios';
import { colors, radius, fonts } from '../constants/theme';

const BASE_URL = 'http://localhost:8000';

export interface VisionResult {
  visible_findings: string[];
  possible_conditions: string[];
  urgency_signal: number;
  confidence: number;
  red_flag_visible: boolean;
  reasoning: string;
  analysis_available: boolean;
}

interface Props {
  zoneId: string;
  onResult: (result: VisionResult) => void;
}

export function ImageUploader({ zoneId, onResult }: Props) {
  const [imageUri, setImageUri] = useState<string | null>(null);
  const [analysing, setAnalysing] = useState(false);
  const [result, setResult] = useState<VisionResult | null>(null);
  const [expanded, setExpanded] = useState(false);

  const pickImage = async () => {
    if (Platform.OS !== 'web') {
      const { status } = await ImagePicker.requestMediaLibraryPermissionsAsync();
      if (status !== 'granted') {
        Alert.alert('Permission needed', 'Camera roll access is required to upload a photo.');
        return;
      }
    }

    const picked = await ImagePicker.launchImageLibraryAsync({
      mediaTypes: ImagePicker.MediaTypeOptions.Images,
      quality: 0.7,
      base64: false,
      allowsEditing: true,
      aspect: [4, 3],
    });

    if (picked.canceled || !picked.assets[0]) return;
    const asset = picked.assets[0];
    setImageUri(asset.uri);
    setResult(null);
    await analyseImage(asset.uri);
  };

  const takePhoto = async () => {
    if (Platform.OS === 'web') { pickImage(); return; }
    const { status } = await ImagePicker.requestCameraPermissionsAsync();
    if (status !== 'granted') {
      Alert.alert('Permission needed', 'Camera access is required to take a photo.');
      return;
    }
    const photo = await ImagePicker.launchCameraAsync({
      quality: 0.7,
      allowsEditing: true,
      aspect: [4, 3],
    });
    if (photo.canceled || !photo.assets[0]) return;
    setImageUri(photo.assets[0].uri);
    setResult(null);
    await analyseImage(photo.assets[0].uri);
  };

  const analyseImage = async (uri: string) => {
    setAnalysing(true);
    try {
      const ext = uri.split('.').pop()?.toLowerCase().split('?')[0] ?? 'jpg';
      const mimeMap: Record<string, string> = {
        jpg: 'image/jpeg', jpeg: 'image/jpeg',
        png: 'image/png', webp: 'image/webp',
      };
      const mime = mimeMap[ext] ?? 'image/jpeg';

      const form = new FormData();

      if (Platform.OS === 'web') {
        // On web, uri is a blob: URL — fetch it and append as a Blob
        const response = await fetch(uri);
        const blob = await response.blob();
        form.append('file', blob, `photo.${ext}`);
      } else {
        // On native, use the RN FormData object trick
        form.append('file', { uri, name: `photo.${ext}`, type: mime } as any);
      }

      form.append('zone_id', zoneId);

      const res = await axios.post<VisionResult>(
        `${BASE_URL}/api/vision/analyse`,
        form,
        {
          // Do NOT manually set Content-Type on web — let the browser set the boundary
          headers: Platform.OS === 'web'
            ? {}
            : { 'Content-Type': 'multipart/form-data' },
          timeout: 20000,
        },
      );

      setResult(res.data);
      onResult(res.data);
    } catch (err) {
      const fallback: VisionResult = {
        visible_findings: [], possible_conditions: [], urgency_signal: 2,
        confidence: 0, red_flag_visible: false,
        reasoning: 'Image analysis unavailable. Continuing with symptom questions.',
        analysis_available: false,
      };
      setResult(fallback);
      onResult(fallback);
    } finally {
      setAnalysing(false);
    }
  };

  const urgencyColor = result
    ? [colors.tier0, colors.tier1, colors.tier2, colors.tier3, colors.tier4][
        Math.min(result.urgency_signal, 4)
      ]
    : colors.teal;

  if (!expanded) {
    return (
      <TouchableOpacity style={styles.collapseBtn} onPress={() => setExpanded(true)}>
        <Ionicons name="camera-outline" size={15} color={colors.textSecondary} />
        <Text style={styles.collapseBtnText}>Add a photo (optional)</Text>
        <Ionicons name="chevron-down" size={13} color={colors.textDim} />
      </TouchableOpacity>
    );
  }

  return (
    <View style={styles.container}>
      <View style={styles.headerRow}>
        <Ionicons name="camera-outline" size={14} color={colors.sky} />
        <Text style={styles.headerText}>Photo analysis</Text>
        <Text style={styles.headerNote}>optional · supplements questionnaire</Text>
        <TouchableOpacity onPress={() => setExpanded(false)} style={{ marginLeft: 'auto' }}>
          <Ionicons name="chevron-up" size={14} color={colors.textDim} />
        </TouchableOpacity>
      </View>

      {!imageUri ? (
        <View style={styles.pickRow}>
          <TouchableOpacity style={styles.pickBtn} onPress={pickImage}>
            <Ionicons name="images-outline" size={18} color={colors.sky} />
            <Text style={styles.pickText}>Choose photo</Text>
          </TouchableOpacity>
          {Platform.OS !== 'web' && (
            <TouchableOpacity style={styles.pickBtn} onPress={takePhoto}>
              <Ionicons name="camera" size={18} color={colors.sky} />
              <Text style={styles.pickText}>Take photo</Text>
            </TouchableOpacity>
          )}
        </View>
      ) : (
        <View style={styles.previewWrapper}>
          <Image source={{ uri: imageUri }} style={styles.preview} resizeMode="cover" />
          {analysing && (
            <View style={styles.analysingOverlay}>
              <ActivityIndicator color={colors.teal} size="small" />
              <Text style={styles.analysingText}>Analysing…</Text>
            </View>
          )}
          <TouchableOpacity style={styles.clearBtn} onPress={() => { setImageUri(null); setResult(null); }}>
            <Ionicons name="close-circle" size={22} color={colors.text} />
          </TouchableOpacity>
        </View>
      )}

      {result && !analysing && (
        <View style={[styles.resultCard, { borderColor: urgencyColor + '40' }]}>
          {result.red_flag_visible && (
            <View style={styles.redFlagRow}>
              <Ionicons name="alert-circle" size={13} color={colors.tier4} />
              <Text style={[styles.resultLabel, { color: colors.tier4 }]}>RED FLAG VISIBLE IN IMAGE</Text>
            </View>
          )}
          {result.visible_findings.length > 0 && (
            <Text style={styles.resultFindings}>
              Findings: {result.visible_findings.join(', ')}
            </Text>
          )}
          {result.possible_conditions.length > 0 && (
            <Text style={styles.resultConditions}>
              May suggest: {result.possible_conditions.join(', ')}
            </Text>
          )}
          <Text style={styles.resultReasoning}>{result.reasoning}</Text>
          <View style={styles.confidenceRow}>
            <View style={[styles.signalDot, { backgroundColor: urgencyColor }]} />
            <Text style={[styles.signalText, { color: urgencyColor }]}>
              Image urgency signal: Level {result.urgency_signal + 1}
            </Text>
            <Text style={styles.confText}>
              {Math.round(result.confidence * 100)}% confidence
            </Text>
          </View>
        </View>
      )}

      <Text style={styles.disclaimer}>
        Image analysis is supplementary. Questionnaire results remain authoritative.
      </Text>
    </View>
  );
}

const styles = StyleSheet.create({
  collapseBtn: {
    flexDirection: 'row', alignItems: 'center', gap: 8,
    paddingVertical: 10, paddingHorizontal: 14,
    backgroundColor: colors.bgCard, borderRadius: radius.md,
    borderWidth: 1, borderColor: colors.border,
  },
  collapseBtnText: { fontFamily: fonts.body, fontSize: 13, color: colors.textSecondary, flex: 1 },
  container: {
    backgroundColor: colors.bgCard, borderRadius: radius.md,
    borderWidth: 1, borderColor: colors.sky + '25', padding: 13, gap: 10,
  },
  headerRow: { flexDirection: 'row', alignItems: 'center', gap: 6 },
  headerText: { fontFamily: fonts.body, fontSize: 12, fontWeight: '600', color: colors.sky },
  headerNote: { fontFamily: fonts.body, fontSize: 10, color: colors.textDim },
  pickRow: { flexDirection: 'row', gap: 10 },
  pickBtn: {
    flex: 1, flexDirection: 'row', alignItems: 'center', justifyContent: 'center',
    gap: 7, backgroundColor: colors.skyDim, borderRadius: radius.md,
    borderWidth: 1, borderColor: colors.sky + '30', paddingVertical: 12,
  },
  pickText: { fontFamily: fonts.body, fontSize: 13, color: colors.sky, fontWeight: '600' },
  previewWrapper: { position: 'relative', height: 140, borderRadius: radius.md, overflow: 'hidden' },
  preview: { width: '100%', height: '100%' },
  analysingOverlay: {
    ...StyleSheet.absoluteFillObject,
    backgroundColor: 'rgba(6,13,20,0.7)',
    alignItems: 'center', justifyContent: 'center', gap: 8,
  },
  analysingText: { fontFamily: fonts.body, fontSize: 13, color: colors.teal },
  clearBtn: { position: 'absolute', top: 6, right: 6 },
  resultCard: {
    backgroundColor: colors.bg, borderRadius: radius.md,
    borderWidth: 1, padding: 11, gap: 6,
  },
  redFlagRow: { flexDirection: 'row', alignItems: 'center', gap: 5 },
  resultLabel: { fontFamily: fonts.body, fontSize: 9, fontWeight: '700', letterSpacing: 1, textTransform: 'uppercase' },
  resultFindings: { fontFamily: fonts.body, fontSize: 12, color: colors.text, lineHeight: 17 },
  resultConditions: { fontFamily: fonts.body, fontSize: 12, color: colors.textSecondary, lineHeight: 17 },
  resultReasoning: { fontFamily: fonts.body, fontSize: 11, color: colors.textDim, lineHeight: 16 },
  confidenceRow: { flexDirection: 'row', alignItems: 'center', gap: 7 },
  signalDot: { width: 6, height: 6, borderRadius: 3 },
  signalText: { fontFamily: fonts.body, fontSize: 11, fontWeight: '600' },
  confText: { fontFamily: fonts.body, fontSize: 10, color: colors.textDim, marginLeft: 'auto' },
  disclaimer: { fontFamily: fonts.body, fontSize: 10, color: colors.textDim, lineHeight: 15 },
});

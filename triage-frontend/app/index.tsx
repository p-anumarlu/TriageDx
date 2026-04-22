import React, { useEffect, useRef } from 'react';
import {
  View, Text, TouchableOpacity, StyleSheet, Animated, SafeAreaView,
} from 'react-native';
import { router } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { BodyDiagram, ZoneId } from '../components/BodyDiagram';
import { colors, radius, fonts } from '../constants/theme';

export default function HomeScreen() {
  const fadeAnim = useRef(new Animated.Value(0)).current;
  const slideAnim = useRef(new Animated.Value(20)).current;

  useEffect(() => {
    Animated.parallel([
      Animated.timing(fadeAnim, { toValue: 1, duration: 600, useNativeDriver: true }),
      Animated.timing(slideAnim, { toValue: 0, duration: 500, useNativeDriver: true }),
    ]).start();
  }, []);

  const handleZonePress = (zoneId: ZoneId) => {
    if (zoneId === 'head') {
      router.push({ pathname: '/head-subzone' });
    } else {
      router.push({ pathname: '/questions', params: { zone: zoneId } });
    }
  };

  return (
    <SafeAreaView style={styles.safe}>
      <View style={styles.container}>
        {/* Header */}
        <Animated.View
          style={[styles.header, { opacity: fadeAnim, transform: [{ translateY: slideAnim }] }]}
        >
          <Text style={styles.logo}>
            triage<Text style={styles.logoAccent}>.ai</Text>
          </Text>
          <Text style={styles.tagline}>Tap where it hurts</Text>
        </Animated.View>

        {/* Body Diagram */}
        <Animated.View style={[styles.diagramWrapper, { opacity: fadeAnim }]}>
          <BodyDiagram onZonePress={handleZonePress} />
        </Animated.View>

        {/* General Symptoms Button */}
        <Animated.View
          style={[styles.bottomArea, { opacity: fadeAnim, transform: [{ translateY: slideAnim }] }]}
        >
          <TouchableOpacity
            style={styles.generalBtn}
            onPress={() => router.push('/general')}
            activeOpacity={0.75}
          >
            <View style={styles.generalIcon}>
              <Ionicons name="body-outline" size={18} color={colors.teal} />
            </View>
            <View style={styles.generalText}>
              <Text style={styles.generalTitle}>General Symptoms</Text>
              <Text style={styles.generalSub}>Fever, fatigue, dizziness, body pain</Text>
            </View>
            <Ionicons name="chevron-forward" size={16} color={colors.textDim} />
          </TouchableOpacity>

          <Text style={styles.disclaimer}>
            Triage guidance only · Not a diagnosis · Always consult a physician
          </Text>
        </Animated.View>
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: {
    flex: 1,
    backgroundColor: colors.bg,
  },
  container: {
    flex: 1,
    paddingHorizontal: 20,
    paddingBottom: 8,
  },
  header: {
    paddingTop: 12,
    paddingBottom: 6,
    alignItems: 'center',
  },
  logo: {
    fontFamily: fonts.serif,
    fontSize: 28,
    color: colors.text,
    fontWeight: '400',
    letterSpacing: -0.5,
  },
  logoAccent: {
    color: colors.teal,
  },
  tagline: {
    fontFamily: fonts.body,
    fontSize: 11,
    color: colors.textSecondary,
    textTransform: 'uppercase',
    letterSpacing: 1.5,
    marginTop: 2,
  },
  diagramWrapper: {
    flex: 1,
    minHeight: 340,
  },
  bottomArea: {
    gap: 10,
    paddingBottom: 4,
  },
  generalBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: colors.bgCard,
    borderRadius: radius.lg,
    borderWidth: 1,
    borderColor: colors.border,
    padding: 14,
    gap: 12,
  },
  generalIcon: {
    width: 38,
    height: 38,
    borderRadius: 19,
    backgroundColor: colors.tealDim,
    borderWidth: 1,
    borderColor: colors.teal + '30',
    alignItems: 'center',
    justifyContent: 'center',
  },
  generalText: {
    flex: 1,
  },
  generalTitle: {
    fontFamily: fonts.body,
    fontSize: 14,
    fontWeight: '600',
    color: colors.text,
    marginBottom: 2,
  },
  generalSub: {
    fontFamily: fonts.body,
    fontSize: 11,
    color: colors.textSecondary,
  },
  disclaimer: {
    fontFamily: fonts.body,
    fontSize: 10,
    color: colors.textDim,
    textAlign: 'center',
    lineHeight: 15,
  },
});

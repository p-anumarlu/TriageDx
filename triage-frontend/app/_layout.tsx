import React, { useEffect, useState } from 'react';
import { Platform, View, StyleSheet } from 'react-native';
import { Stack, router } from 'expo-router';
import { useFonts } from 'expo-font';
import * as SplashScreen from 'expo-splash-screen';
import { StatusBar } from 'expo-status-bar';
import { PhoneFrame } from '../components/PhoneFrame';
import { colors } from '../constants/theme';
import { api, ProfilePayload } from '../lib/api';

SplashScreen.preventAutoHideAsync();

export default function RootLayout() {
  const [loaded] = useFonts({
    'Manrope-Regular': { uri: 'https://fonts.gstatic.com/s/manrope/v15/xn7gYHE41ni1AdIRggixSuXd.woff2' },
    'Manrope-SemiBold': { uri: 'https://fonts.gstatic.com/s/manrope/v15/xn7gYHE41ni1AdIRggOxSuXd.woff2' },
  } as any);

  const [profileChecked, setProfileChecked] = useState(false);

  useEffect(() => {
    if (!loaded) return;
    api.getProfile()
      .then((p: ProfilePayload) => {
        if (!p.onboarding_complete) {
          router.replace('/onboarding');
        }
      })
      .catch(() => {
        // Anonymous user or not authenticated — skip onboarding gate
      })
      .finally(() => setProfileChecked(true));
  }, [loaded]);

  useEffect(() => {
    if (loaded && profileChecked) SplashScreen.hideAsync();
  }, [loaded, profileChecked]);

  if (!loaded || !profileChecked) return null;

  const nav = (
    <Stack
      screenOptions={{
        headerShown: false,
        contentStyle: { backgroundColor: colors.bg },
        animation: 'fade',
      }}
    />
  );

  if (Platform.OS === 'web') {
    return (
      <>
        <StatusBar style="light" />
        <PhoneFrame>
          <View style={styles.inner}>{nav}</View>
        </PhoneFrame>
      </>
    );
  }

  return (
    <>
      <StatusBar style="light" />
      {nav}
    </>
  );
}

const styles = StyleSheet.create({
  inner: {
    flex: 1,
    backgroundColor: colors.bg,
  },
});
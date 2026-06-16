import React from "react";
import { NavigationContainer } from "@react-navigation/native";
import { createNativeStackNavigator } from "@react-navigation/native-stack";
import { createBottomTabNavigator } from "@react-navigation/bottom-tabs";
import { View, Text, StyleSheet } from "react-native";
import { useStore } from "../store/useStore";

import LoginScreen from "../screens/LoginScreen";
import HomeScreen from "../screens/HomeScreen";
import UploadScreen from "../screens/UploadScreen";
import AnalysisProgressScreen from "../screens/AnalysisProgressScreen";
import AssessmentScreen from "../screens/AssessmentScreen";
import TrainingPlanScreen from "../screens/TrainingPlanScreen";
import HistoryScreen from "../screens/HistoryScreen";
import ProfileScreen from "../screens/ProfileScreen";

const C = { bg: "#0A0D14", accent: "#00D68F", muted: "#6B7280" };

const TabIcon = ({ label, focused }: { label: string; focused: boolean }) => {
  const icons: Record<string, string> = { Home: "🏠", History: "📋", Profile: "👤" };
  return (
    <View style={tabStyles.icon}>
      <Text style={{ fontSize: 18 }}>{icons[label] || "•"}</Text>
    </View>
  );
};

const tabStyles = StyleSheet.create({ icon: { alignItems: "center", justifyContent: "center" } });

const Stack = createNativeStackNavigator();
const Tab = createBottomTabNavigator();

function MainTabs() {
  return (
    <Tab.Navigator screenOptions={{
      headerShown: false,
      tabBarStyle: { backgroundColor: "#111827", borderTopColor: "#1F2937", borderTopWidth: 1, height: 60, paddingBottom: 8 },
      tabBarActiveTintColor: C.accent,
      tabBarInactiveTintColor: C.muted,
      tabBarLabelStyle: { fontSize: 11, fontWeight: "600" },
    }}>
      <Tab.Screen name="Home" component={HomeScreen} options={{ tabBarIcon: ({ focused }) => <TabIcon label="Home" focused={focused} /> }} />
      <Tab.Screen name="History" component={HistoryScreen} options={{ tabBarIcon: ({ focused }) => <TabIcon label="History" focused={focused} /> }} />
      <Tab.Screen name="Profile" component={ProfileScreen} options={{ tabBarIcon: ({ focused }) => <TabIcon label="Profile" focused={focused} /> }} />
    </Tab.Navigator>
  );
}

export default function RootNavigator() {
  const isLoggedIn = useStore((s) => s.isLoggedIn);
  return (
    <NavigationContainer theme={{ dark: true, colors: { primary: C.accent, background: C.bg, card: "#111827", text: "#FFFFFF", border: "#1F2937", notification: C.accent } }}>
      <Stack.Navigator screenOptions={{ headerShown: false, contentStyle: { backgroundColor: C.bg } }}>
        {!isLoggedIn ? (
          <Stack.Screen name="Login" component={LoginScreen} />
        ) : (
          <>
            <Stack.Screen name="Main" component={MainTabs} />
            <Stack.Screen name="Upload" component={UploadScreen} />
            <Stack.Screen name="AnalysisProgress" component={AnalysisProgressScreen} />
            <Stack.Screen name="Assessment" component={AssessmentScreen} />
            <Stack.Screen name="TrainingPlan" component={TrainingPlanScreen} />
          </>
        )}
      </Stack.Navigator>
    </NavigationContainer>
  );
}

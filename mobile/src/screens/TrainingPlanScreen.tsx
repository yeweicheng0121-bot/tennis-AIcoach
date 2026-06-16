import React, { useEffect, useState } from "react";
import { View, Text, StyleSheet, ScrollView, ActivityIndicator } from "react-native";
import { getTrainingPlan } from "../services/api";

export default function TrainingPlanScreen({ route }: any) {
  const { id } = route.params;
  const [plan, setPlan] = useState<any>(null);
  useEffect(() => { getTrainingPlan(id).then(setPlan); }, [id]);
  if (!plan) return <ActivityIndicator size="large" style={{ marginTop: 100 }} />;

  return (
    <ScrollView style={s.wrap}>
      <Text style={s.title}>Training Plan</Text>
      <Text style={s.sub}>{plan.duration_weeks} weeks · {plan.sessions_per_week}/week</Text>
      {plan.primary_goals && <View style={s.sec}><Text style={s.secT}>🎯 Goals</Text><Text>{JSON.stringify(plan.primary_goals)}</Text></View>}
      {plan.weekly_plans && <View style={s.sec}><Text style={s.secT}>📅 Weekly</Text><Text>{JSON.stringify(plan.weekly_plans)}</Text></View>}
      <View style={{ height: 60 }} />
    </ScrollView>
  );
}

const s = StyleSheet.create({
  wrap: { flex: 1, backgroundColor: "#f5f5f5", padding: 16 },
  title: { fontSize: 22, fontWeight: "bold", marginTop: 40, marginBottom: 8 },
  sub: { fontSize: 15, color: "#666", marginBottom: 16 },
  sec: { backgroundColor: "#fff", borderRadius: 12, padding: 16, marginBottom: 12 },
  secT: { fontSize: 16, fontWeight: "600", marginBottom: 8 },
});

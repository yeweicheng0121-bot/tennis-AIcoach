import React, { useEffect, useState } from "react";
import { View, Text, StyleSheet, ScrollView, ActivityIndicator } from "react-native";
import { getTrainingPlan } from "../services/api";

const C = { bg: "#0A0D14", card: "#111827", accent: "#00D68F", text: "#FFFFFF", muted: "#6B7280", sub: "#9CA3AF", border: "#1F2937" };

export default function TrainingPlanScreen({ route }: any) {
  const { id } = route.params;
  const [plan, setPlan] = useState<any>(null);
  useEffect(() => { getTrainingPlan(id).then(setPlan); }, [id]);
  if (!plan) return <ActivityIndicator size="large" color={C.accent} style={{ marginTop: 120 }} />;

  return (
    <ScrollView style={styles.wrap} contentContainerStyle={{ paddingBottom: 60 }}>
      <Text style={styles.title}>Training Plan</Text>
      <View style={styles.header}>
        <View style={styles.stat}><Text style={styles.statNum}>{plan.duration_weeks}</Text><Text style={styles.statLabel}>Weeks</Text></View>
        <View style={styles.divider} />
        <View style={styles.stat}><Text style={styles.statNum}>{plan.sessions_per_week}</Text><Text style={styles.statLabel}>Per Week</Text></View>
      </View>
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Goals</Text>
        <Text style={styles.body}>{JSON.stringify(plan.primary_goals, null, 2)}</Text>
      </View>
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Weekly Schedule</Text>
        <Text style={styles.body}>{JSON.stringify(plan.weekly_plans, null, 2)}</Text>
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  wrap: { flex: 1, backgroundColor: C.bg, padding: 20 },
  title: { fontSize: 28, fontWeight: "800", color: C.text, marginTop: 50, marginBottom: 20 },
  header: { backgroundColor: C.card, borderRadius: 20, padding: 24, flexDirection: "row", alignItems: "center", justifyContent: "center", marginBottom: 16, borderWidth: 1, borderColor: C.border },
  stat: { flex: 1, alignItems: "center" },
  statNum: { fontSize: 40, fontWeight: "800", color: C.accent },
  statLabel: { fontSize: 12, color: C.muted, marginTop: 4, letterSpacing: 1 },
  divider: { width: 1, height: 40, backgroundColor: C.border },
  section: { backgroundColor: C.card, borderRadius: 16, padding: 18, marginBottom: 12, borderWidth: 1, borderColor: C.border },
  sectionTitle: { fontSize: 13, fontWeight: "700", color: C.sub, letterSpacing: 1.5, marginBottom: 10, textTransform: "uppercase" },
  body: { fontSize: 13, color: C.sub, lineHeight: 20 },
});

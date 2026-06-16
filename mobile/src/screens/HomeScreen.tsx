import React, { useEffect, useState } from "react";
import { View, Text, StyleSheet, TouchableOpacity, ScrollView } from "react-native";
import { useStore } from "../store/useStore";
import { listAssessments, listTrainingPlans } from "../services/api";

const C = { bg: "#0A0D14", card: "#111827", accent: "#00D68F", text: "#FFFFFF", muted: "#6B7280", sub: "#9CA3AF", border: "#1F2937" };

export default function HomeScreen({ navigation }: any) {
  const user = useStore((s) => s.user);
  const [latest, setLatest] = useState<any>(null);
  const [plan, setPlan] = useState<any>(null);

  useEffect(() => {
    listAssessments().then(l => { if (l.length) setLatest(l[0]); });
    listTrainingPlans().then(l => { if (l.length) setPlan(l[0]); });
  }, []);

  return (
    <ScrollView style={styles.wrap} contentContainerStyle={{ paddingBottom: 40 }}>
      <Text style={styles.greeting}>Hi, {user?.nickname || "Player"} 👋</Text>

      {latest ? (
        <TouchableOpacity style={styles.ntrpCard} onPress={() => navigation.navigate("Assessment", { id: latest.assessment_id })} activeOpacity={0.8}>
          <Text style={styles.ntrpLabel}>LATEST RATING</Text>
          <Text style={styles.ntrpValue}>NTRP {latest.overall_ntrp ?? "—"}</Text>
          <Text style={styles.ntrpConf}>{latest.ntrp_confidence ? `${(latest.ntrp_confidence * 100).toFixed(0)}% confidence` : ""}</Text>
          <View style={styles.tagRow}>
            {(latest.strengths || []).slice(0, 2).map((s: string, i: number) => <View key={i} style={styles.tagGreen}><Text style={styles.tagText}>✓ {s}</Text></View>)}
          </View>
        </TouchableOpacity>
      ) : (
        <View style={styles.emptyCard}>
          <Text style={styles.emptyIcon}>📹</Text>
          <Text style={styles.emptyTitle}>No Assessments Yet</Text>
          <Text style={styles.emptySub}>Upload your first tennis video to get{'\n'}an AI-powered NTRP rating</Text>
        </View>
      )}

      {plan && (
        <View style={styles.card}>
          <Text style={styles.cardTitle}>Active Training Plan</Text>
          <View style={styles.planRow}>
            <View style={styles.planStat}><Text style={styles.planNum}>{plan.duration_weeks}</Text><Text style={styles.planUnit}>weeks</Text></View>
            <View style={styles.planDiv} />
            <View style={styles.planStat}><Text style={styles.planNum}>{plan.sessions_per_week}</Text><Text style={styles.planUnit}>/ week</Text></View>
          </View>
        </View>
      )}

      <TouchableOpacity style={styles.uploadBtn} onPress={() => navigation.navigate("Upload")} activeOpacity={0.8}>
        <Text style={styles.uploadIcon}>+</Text>
        <Text style={styles.uploadText}>New Analysis</Text>
      </TouchableOpacity>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  wrap: { flex: 1, backgroundColor: C.bg, padding: 20 },
  greeting: { fontSize: 26, fontWeight: "700", color: C.text, marginTop: 50, marginBottom: 24 },
  ntrpCard: { backgroundColor: "rgba(0,214,143,0.1)", borderRadius: 20, padding: 24, marginBottom: 16, borderWidth: 1, borderColor: "rgba(0,214,143,0.2)" },
  ntrpLabel: { fontSize: 11, fontWeight: "600", color: C.accent, letterSpacing: 2, marginBottom: 8 },
  ntrpValue: { fontSize: 52, fontWeight: "800", color: C.accent, letterSpacing: -1 },
  ntrpConf: { fontSize: 13, color: C.muted, marginTop: 4 },
  tagRow: { flexDirection: "row", marginTop: 14, gap: 8 },
  tagGreen: { backgroundColor: "rgba(0,214,143,0.15)", paddingHorizontal: 12, paddingVertical: 6, borderRadius: 8 },
  tagText: { color: C.accent, fontSize: 12, fontWeight: "600" },
  emptyCard: { backgroundColor: C.card, borderRadius: 20, padding: 32, alignItems: "center", marginBottom: 16, borderWidth: 1, borderColor: C.border },
  emptyIcon: { fontSize: 40, marginBottom: 12 },
  emptyTitle: { fontSize: 18, fontWeight: "700", color: C.text, marginBottom: 6 },
  emptySub: { fontSize: 13, color: C.muted, textAlign: "center", lineHeight: 19 },
  card: { backgroundColor: C.card, borderRadius: 18, padding: 20, marginBottom: 16, borderWidth: 1, borderColor: C.border },
  cardTitle: { fontSize: 14, fontWeight: "600", color: C.sub, marginBottom: 16, letterSpacing: 1 },
  planRow: { flexDirection: "row", alignItems: "center" },
  planStat: { flex: 1, alignItems: "center" },
  planNum: { fontSize: 36, fontWeight: "800", color: C.text },
  planUnit: { fontSize: 12, color: C.muted, marginTop: 2 },
  planDiv: { width: 1, height: 40, backgroundColor: C.border },
  uploadBtn: { backgroundColor: C.accent, borderRadius: 18, padding: 20, flexDirection: "row", alignItems: "center", justifyContent: "center", marginTop: 8, gap: 10 },
  uploadIcon: { fontSize: 22, fontWeight: "300", color: "#0A0D14" },
  uploadText: { fontSize: 17, fontWeight: "700", color: "#0A0D14" },
});

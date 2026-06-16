import React, { useEffect, useState } from "react";
import { View, Text, StyleSheet, ScrollView, ActivityIndicator } from "react-native";
import { getAssessment } from "../services/api";
import RadarChart from "../components/RadarChart";

const C = { bg: "#0A0D14", card: "#111827", accent: "#00D68F", text: "#FFFFFF", muted: "#6B7280", sub: "#9CA3AF", border: "#1F2937", red: "#EF4444", amber: "#F59E0B" };

export default function AssessmentScreen({ route }: any) {
  const { id } = route.params;
  const [a, setA] = useState<any>(null);
  useEffect(() => { getAssessment(id).then(setA); }, [id]);
  if (!a) return <ActivityIndicator size="large" color={C.accent} style={{ marginTop: 120 }} />;

  const tech = a.technique_breakdown || {};
  const fit = a.fitness_breakdown || {};
  const hasFitness = fit?.cardiovascular_endurance;

  return (
    <ScrollView style={styles.wrap} contentContainerStyle={{ paddingBottom: 60 }}>
      <Text style={styles.title}>Assessment</Text>

      <View style={styles.ntrpCard}>
        <Text style={styles.ntrpLabel}>YOUR RATING</Text>
        <Text style={styles.ntrpValue}>{a.overall_ntrp ? `NTRP ${a.overall_ntrp}` : "Insufficient\nData"}</Text>
        <Text style={styles.conf}>{(a.ntrp_confidence ? a.ntrp_confidence * 100 : 0).toFixed(0)}% confidence</Text>
      </View>

      <RadarChart data={{
        Forehand: tech?.forehand?.score || 0,
        Backhand: tech?.backhand?.score || 0,
        Serve: tech?.serve?.score || 0,
        Volley: tech?.volley?.score || 0,
        Footwork: tech?.footwork?.score || 0,
        Return: tech?.return?.score || 0,
      }} />

      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Strengths</Text>
        {(a.strengths || []).map((s: string, i: number) => <View key={i} style={styles.bullet}><View style={styles.bulletDotGreen} /><Text style={styles.bulletText}>{s}</Text></View>)}
        {(!a.strengths || a.strengths.length === 0) && <Text style={styles.empty}>—</Text>}
      </View>

      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Areas to Improve</Text>
        {(a.weaknesses || []).map((w: string, i: number) => <View key={i} style={styles.bullet}><View style={styles.bulletDotRed} /><Text style={styles.bulletText}>{w}</Text></View>)}
        {(!a.weaknesses || a.weaknesses.length === 0) && <Text style={styles.empty}>—</Text>}
      </View>

      {hasFitness ? (
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Fitness</Text>
          <View style={styles.fitnessRow}>
            <View style={styles.fitItem}><Text style={styles.fitNum}>{fit.cardiovascular_endurance?.score || "—"}</Text><Text style={styles.fitLabel}>Cardio</Text></View>
            <View style={styles.fitItem}><Text style={styles.fitNum}>{fit.movement?.score || "—"}</Text><Text style={styles.fitLabel}>Movement</Text></View>
            <View style={styles.fitItem}><Text style={styles.fitNum}>{fit.training_load?.score || "—"}</Text><Text style={styles.fitLabel}>Load</Text></View>
          </View>
        </View>
      ) : a.report_markdown?.includes("no watch data") ? null : null}

      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Full Report</Text>
        <Text style={styles.reportText}>{(a.report_markdown || "").slice(0, 3000)}</Text>
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  wrap: { flex: 1, backgroundColor: C.bg, padding: 20 },
  title: { fontSize: 28, fontWeight: "800", color: C.text, marginTop: 50, marginBottom: 20 },
  ntrpCard: { backgroundColor: "rgba(0,214,143,0.08)", borderRadius: 24, padding: 28, alignItems: "center", marginBottom: 16, borderWidth: 1, borderColor: "rgba(0,214,143,0.15)" },
  ntrpLabel: { fontSize: 11, fontWeight: "600", color: C.accent, letterSpacing: 3, marginBottom: 12 },
  ntrpValue: { fontSize: 48, fontWeight: "800", color: C.accent, textAlign: "center", lineHeight: 52 },
  conf: { fontSize: 13, color: C.muted, marginTop: 8 },
  section: { backgroundColor: C.card, borderRadius: 16, padding: 18, marginBottom: 12, borderWidth: 1, borderColor: C.border },
  sectionTitle: { fontSize: 13, fontWeight: "700", color: C.sub, letterSpacing: 1.5, marginBottom: 12, textTransform: "uppercase" },
  bullet: { flexDirection: "row", alignItems: "center", marginBottom: 8 },
  bulletDotGreen: { width: 8, height: 8, borderRadius: 4, backgroundColor: C.accent, marginRight: 10 },
  bulletDotRed: { width: 8, height: 8, borderRadius: 4, backgroundColor: C.amber, marginRight: 10 },
  bulletText: { fontSize: 15, color: C.text },
  empty: { color: C.muted, fontSize: 13 },
  fitnessRow: { flexDirection: "row", justifyContent: "space-around" },
  fitItem: { alignItems: "center" },
  fitNum: { fontSize: 28, fontWeight: "800", color: C.text },
  fitLabel: { fontSize: 11, color: C.muted, marginTop: 4 },
  reportText: { fontSize: 13, color: C.sub, lineHeight: 20 },
});

import React, { useEffect, useState } from "react";
import { View, Text, StyleSheet, ScrollView, ActivityIndicator } from "react-native";
import { getAssessment } from "../services/api";
import RadarChart from "../components/RadarChart";

export default function AssessmentScreen({ route }: any) {
  const { id } = route.params;
  const [a, setA] = useState<any>(null);
  useEffect(() => { getAssessment(id).then(setA); }, [id]);
  if (!a) return <ActivityIndicator size="large" color="#4CAF50" style={{ marginTop: 100 }} />;

  const tech = a.technique_breakdown || {};
  const fit = a.fitness_breakdown || {};

  return (
    <ScrollView style={s.wrap}>
      <Text style={s.title}>Assessment</Text>
      <View style={s.ntrpCard}>
        <Text style={s.ntrpL}>Overall</Text>
        <Text style={s.ntrpV}>NTRP {a.overall_ntrp}</Text>
        <Text style={s.conf}>{((a.ntrp_confidence || 0) * 100).toFixed(0)}% confidence</Text>
      </View>
      <RadarChart data={{ FH: tech?.forehand?.score || 0, BH: tech?.backhand?.score || 0, Serve: tech?.serve?.score || 0, Volley: tech?.volley?.score || 0, Footwork: tech?.footwork?.score || 0, Return: tech?.return?.score || 0 }} />
      <View style={s.sec}><Text style={s.secT}>✅ Strengths</Text>{(a.strengths || []).map((x: string, i: number) => <Text key={i}>• {x}</Text>)}</View>
      <View style={s.sec}><Text style={s.secT}>⚠️ Weaknesses</Text>{(a.weaknesses || []).map((x: string, i: number) => <Text key={i}>• {x}</Text>)}</View>
      {fit?.cardiovascular_endurance && <View style={s.sec}><Text style={s.secT}>💪 Fitness</Text><Text>Cardio: {fit.cardiovascular_endurance.score}</Text><Text>Movement: {fit.movement?.score}</Text></View>}
      <View style={s.sec}><Text style={s.secT}>Report</Text><Text style={s.rpt}>{(a.report_markdown || "").slice(0, 2000)}</Text></View>
      <View style={{ height: 60 }} />
    </ScrollView>
  );
}

const s = StyleSheet.create({
  wrap: { flex: 1, backgroundColor: "#f5f5f5", padding: 16 },
  title: { fontSize: 22, fontWeight: "bold", marginTop: 40, marginBottom: 16 },
  ntrpCard: { backgroundColor: "#4CAF50", borderRadius: 16, padding: 24, alignItems: "center", marginBottom: 16 },
  ntrpL: { color: "#fff", fontSize: 14 }, ntrpV: { color: "#fff", fontSize: 56, fontWeight: "bold" }, conf: { color: "#fff", fontSize: 14, marginTop: 4 },
  sec: { backgroundColor: "#fff", borderRadius: 12, padding: 16, marginBottom: 12 },
  secT: { fontSize: 16, fontWeight: "600", marginBottom: 8 },
  rpt: { fontSize: 14, lineHeight: 20, color: "#555" },
});

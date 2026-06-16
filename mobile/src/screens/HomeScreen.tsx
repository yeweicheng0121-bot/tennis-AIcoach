import React, { useEffect, useState } from "react";
import { View, Text, StyleSheet, TouchableOpacity, ScrollView } from "react-native";
import { useStore } from "../store/useStore";
import { listAssessments, listTrainingPlans } from "../services/api";

export default function HomeScreen({ navigation }: any) {
  const user = useStore((s) => s.user);
  const [latest, setLatest] = useState<any>(null);
  const [plan, setPlan] = useState<any>(null);

  useEffect(() => {
    listAssessments().then(l => { if (l.length) setLatest(l[0]); });
    listTrainingPlans().then(l => { if (l.length) setPlan(l[0]); });
  }, []);

  return (
    <ScrollView style={s.wrap}>
      <Text style={s.greet}>Hello, {user?.nickname || "Player"}</Text>
      {latest ? (
        <View style={s.card}>
          <Text style={s.cardTitle}>Latest Assessment</Text>
          <Text style={s.ntrp}>NTRP {latest.overall_ntrp}</Text>
          <TouchableOpacity onPress={() => navigation.navigate("Assessment", { id: latest.assessment_id })}>
            <Text style={s.link}>View Report →</Text>
          </TouchableOpacity>
        </View>
      ) : (
        <View style={s.card}><Text style={s.cardTitle}>No assessments yet</Text></View>
      )}
      {plan && (
        <View style={s.card}>
          <Text style={s.cardTitle}>Training Plan</Text>
          <Text>{plan.duration_weeks} weeks · {plan.sessions_per_week}/week</Text>
        </View>
      )}
      <TouchableOpacity style={s.upBtn} onPress={() => navigation.navigate("Upload")}>
        <Text style={s.upBtnText}>+ Upload Video</Text>
      </TouchableOpacity>
    </ScrollView>
  );
}

const s = StyleSheet.create({
  wrap: { flex: 1, backgroundColor: "#f5f5f5", padding: 16 },
  greet: { fontSize: 24, fontWeight: "bold", marginBottom: 20, marginTop: 40 },
  card: { backgroundColor: "#fff", borderRadius: 12, padding: 20, marginBottom: 16, elevation: 2 },
  cardTitle: { fontSize: 16, fontWeight: "600", marginBottom: 8, color: "#666" },
  ntrp: { fontSize: 48, fontWeight: "bold", color: "#4CAF50", marginVertical: 8 },
  link: { color: "#4CAF50", fontSize: 15, marginTop: 12 },
  upBtn: { backgroundColor: "#4CAF50", borderRadius: 12, padding: 18, alignItems: "center", marginBottom: 40 },
  upBtnText: { color: "#fff", fontSize: 18, fontWeight: "600" },
});
